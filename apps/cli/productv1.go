package main

// S04 is a thin client of the existing authenticated Host. It owns no worker,
// process, task database, scheduler or provider configuration.
import (
	"bytes"
	"context"
	"encoding/json"
	"encoding/json/jsontext"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"os/signal"
	"regexp"
	"strconv"
	"strings"
	"sync"
	"time"
	"unicode"
	"unicode/utf8"

	"github.com/santhosh-tekuri/jsonschema/v6"
	rt "researchos.local/research-os/adapters/runtime"
	"researchos.local/research-os/internal/domain"
	"researchos.local/research-os/internal/host"
)

// Exact active rev2 snapshot: 046a49b2b1f82593fe86924913b2ee4d77152ac1cef7dbbb86562f6dfe0cfa1c.
// Inline so an installed CLI never loads a schema from its working directory.
const cliHarnessContract = "{\n  \"contract_id\": \"researchos.host-harness.v1\",\n  \"contract_revision\": 2,\n  \"status\": \"ROOT_FROZEN_IMPLEMENTATION_INTERFACE_NOT_RUNTIME_QUALIFICATION\",\n  \"api_prefix\": \"/harness/v1\",\n  \"wire_version\": \"harness.v1\",\n  \"encoding\": \"UTF-8 JSON; JSON bodies reject duplicate and unknown fields.\",\n  \"scope\": \"One Codex readonly ephemeral turn through the existing Coordinator, canonical Task/Run/lease/dispatch/receipt/outbox/idempotency. Existing V2/Mu contracts unchanged; no parallel business DB or scheduler.\",\n  \"routes\": [\n    {\n      \"method\": \"GET\",\n      \"path\": \"/harness/v1/capabilities\",\n      \"query\": {},\n      \"success_status\": 200,\n      \"response\": \"CapabilitiesResponse\",\n      \"semantics\": \"Metadata query never launches a CLI, prompt, model, login or qualification.\"\n    },\n    {\n      \"method\": \"POST\",\n      \"path\": \"/harness/v1/tasks\",\n      \"request\": \"SubmitRequest\",\n      \"success_status\": 202,\n      \"response\": \"SubmitResponse\",\n      \"semantics\": \"Atomic original Task creation and request idempotency only. Returns QUEUED/run=null. Sole Coordinator.Scan claims/creates Run and launches after commit.\"\n    },\n    {\n      \"method\": \"GET\",\n      \"path\": \"/harness/v1/tasks\",\n      \"query\": {\n        \"project_id\": {\n          \"required\": true,\n          \"type\": \"string\"\n        },\n        \"cursor\": {\n          \"required\": false,\n          \"type\": \"Decimal\",\n          \"default\": \"0\"\n        },\n        \"limit\": {\n          \"required\": false,\n          \"type\": \"integer\",\n          \"default\": 20,\n          \"minimum\": 1,\n          \"maximum\": 100\n        },\n        \"request_id\": {\n          \"required\": false,\n          \"type\": \"RequestID\"\n        }\n      },\n      \"success_status\": 200,\n      \"response\": \"ListResponse\",\n      \"semantics\": \"Authoritative persisted recent-task list. Initial cursor0 lists newest first; subsequent decimal cursor is an exclusive older creation boundary. Exact request_id lookup ignores pagination and returns FOUND or NOT_FOUND.\"\n    },\n    {\n      \"method\": \"GET\",\n      \"path\": \"/harness/v1/tasks/{task_id}\",\n      \"query\": {\n        \"project_id\": {\n          \"required\": true,\n          \"type\": \"string\"\n        }\n      },\n      \"success_status\": 200,\n      \"response\": \"TaskResponse\",\n      \"semantics\": \"Read authoritative Task/active Run/revision and final message. No renderer cache authority.\"\n    },\n    {\n      \"method\": \"GET\",\n      \"path\": \"/harness/v1/tasks/{task_id}/events\",\n      \"query\": {\n        \"project_id\": {\n          \"required\": true,\n          \"type\": \"string\"\n        },\n        \"cursor\": {\n          \"required\": false,\n          \"type\": \"Decimal\",\n          \"default\": \"0\"\n        },\n        \"limit\": {\n          \"required\": false,\n          \"type\": \"integer\",\n          \"default\": 100,\n          \"minimum\": 1,\n          \"maximum\": 500\n        }\n      },\n      \"success_status\": 200,\n      \"response\": \"EventsResponse\",\n      \"semantics\": \"Non-blocking durable event page, ascending sequence strictly after cursor. First release uses polling, not SSE; empty live pages may be retried with bounded backoff.\"\n    },\n    {\n      \"method\": \"POST\",\n      \"path\": \"/harness/v1/tasks/{task_id}/cancel\",\n      \"query\": {\n        \"project_id\": {\n          \"required\": true,\n          \"type\": \"string\"\n        }\n      },\n      \"request\": \"CancelRequest\",\n      \"success_status\": 200,\n      \"response\": \"CancelResponse\",\n      \"semantics\": \"Atomic compare-and-set against actual Task revision and Run/epoch; never renderer-trusted. Cancellation request is not proof of stopped process.\"\n    }\n  ],\n  \"$schema\": \"https://json-schema.org/draft/2020-12/schema\",\n  \"$defs\": {\n    \"Decimal\": {\n      \"type\": \"string\",\n      \"pattern\": \"^(0|[1-9][0-9]{0,18})$\",\n      \"x-int64-max\": \"9223372036854775807\"\n    },\n    \"PositiveDecimal\": {\n      \"type\": \"string\",\n      \"pattern\": \"^[1-9][0-9]{0,18}$\",\n      \"x-int64-max\": \"9223372036854775807\"\n    },\n    \"TaskRef\": {\n      \"type\": \"object\",\n      \"additionalProperties\": false,\n      \"properties\": {\n        \"project_id\": {\n          \"type\": \"string\",\n          \"minLength\": 1,\n          \"maxLength\": 128\n        },\n        \"task_id\": {\n          \"type\": \"string\",\n          \"minLength\": 1,\n          \"maxLength\": 128\n        }\n      },\n      \"required\": [\n        \"project_id\",\n        \"task_id\"\n      ]\n    },\n    \"RunRef\": {\n      \"type\": \"object\",\n      \"additionalProperties\": false,\n      \"properties\": {\n        \"run_id\": {\n          \"type\": \"string\",\n          \"minLength\": 1,\n          \"maxLength\": 128\n        },\n        \"epoch\": {\n          \"$ref\": \"#/$defs/PositiveDecimal\"\n        }\n      },\n      \"required\": [\n        \"run_id\",\n        \"epoch\"\n      ]\n    },\n    \"RequestID\": {\n      \"type\": \"string\",\n      \"pattern\": \"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$\"\n    },\n    \"Error\": {\n      \"type\": \"object\",\n      \"additionalProperties\": false,\n      \"properties\": {\n        \"code\": {\n          \"enum\": [\n            \"INVALID_REQUEST\",\n            \"HOST_AUTH_REQUIRED\",\n            \"FORBIDDEN\",\n            \"NOT_FOUND\",\n            \"STATE_CONFLICT\",\n            \"IDEMPOTENCY_CONFLICT\",\n            \"UNSUPPORTED_CAPABILITY\",\n            \"HARNESS_UNAVAILABLE\",\n            \"HARNESS_AUTH_REQUIRED\",\n            \"WORKSPACE_REVOKED\",\n            \"EXECUTION_UNKNOWN\",\n            \"INTERNAL_ERROR\"\n          ]\n        },\n        \"message\": {\n          \"type\": \"string\",\n          \"maxLength\": 1024\n        },\n        \"retryable\": {\n          \"type\": \"boolean\"\n        },\n        \"task_ref\": {\n          \"anyOf\": [\n            {\n              \"$ref\": \"#/$defs/TaskRef\"\n            },\n            {\n              \"type\": \"null\"\n            }\n          ]\n        },\n        \"current_task_revision\": {\n          \"anyOf\": [\n            {\n              \"$ref\": \"#/$defs/PositiveDecimal\"\n            },\n            {\n              \"type\": \"null\"\n            }\n          ]\n        },\n        \"current_run\": {\n          \"anyOf\": [\n            {\n              \"$ref\": \"#/$defs/RunRef\"\n            },\n            {\n              \"type\": \"null\"\n            }\n          ]\n        }\n      },\n      \"required\": [\n        \"code\",\n        \"message\",\n        \"retryable\",\n        \"task_ref\",\n        \"current_task_revision\",\n        \"current_run\"\n      ]\n    },\n    \"ErrorResponse\": {\n      \"type\": \"object\",\n      \"additionalProperties\": false,\n      \"properties\": {\n        \"api_version\": {\n          \"const\": \"harness.v1\"\n        },\n        \"error\": {\n          \"$ref\": \"#/$defs/Error\"\n        }\n      },\n      \"required\": [\n        \"api_version\",\n        \"error\"\n      ]\n    },\n    \"Capabilities\": {\n      \"type\": \"object\",\n      \"additionalProperties\": false,\n      \"properties\": {\n        \"harness_id\": {\n          \"const\": \"codex\"\n        },\n        \"display_name\": {\n          \"const\": \"Codex CLI\"\n        },\n        \"backend\": {\n          \"const\": \"codex-cli-readonly-v1\"\n        },\n        \"installation\": {\n          \"type\": \"object\",\n          \"additionalProperties\": false,\n          \"properties\": {\n            \"present\": {\n              \"type\": \"boolean\"\n            },\n            \"version\": {\n              \"anyOf\": [\n                {\n                  \"type\": \"string\",\n                  \"minLength\": 1,\n                  \"maxLength\": 128\n                },\n                {\n                  \"type\": \"null\"\n                }\n              ]\n            },\n            \"executable_sha256\": {\n              \"anyOf\": [\n                {\n                  \"type\": \"string\",\n                  \"pattern\": \"^sha256:[0-9a-f]{64}$\"\n                },\n                {\n                  \"type\": \"null\"\n                }\n              ]\n            },\n            \"checked_at\": {\n              \"anyOf\": [\n                {\n                  \"type\": \"string\",\n                  \"format\": \"date-time\"\n                },\n                {\n                  \"type\": \"null\"\n                }\n              ]\n            }\n          },\n          \"required\": [\n            \"present\",\n            \"version\",\n            \"executable_sha256\",\n            \"checked_at\"\n          ]\n        },\n        \"authentication\": {\n          \"type\": \"object\",\n          \"additionalProperties\": false,\n          \"properties\": {\n            \"state\": {\n              \"enum\": [\n                \"UNPROBED\",\n                \"LOGGED_IN\",\n                \"LOGGED_OUT\",\n                \"ERROR\"\n              ]\n            },\n            \"kind\": {\n              \"anyOf\": [\n                {\n                  \"enum\": [\n                    \"chatgpt\",\n                    \"api_key\",\n                    \"other\"\n                  ]\n                },\n                {\n                  \"type\": \"null\"\n                }\n              ]\n            },\n            \"checked_at\": {\n              \"anyOf\": [\n                {\n                  \"type\": \"string\",\n                  \"format\": \"date-time\"\n                },\n                {\n                  \"type\": \"null\"\n                }\n              ]\n            }\n          },\n          \"required\": [\n            \"state\",\n            \"kind\",\n            \"checked_at\"\n          ]\n        },\n        \"verification\": {\n          \"type\": \"object\",\n          \"additionalProperties\": false,\n          \"properties\": {\n            \"execution\": {\n              \"enum\": [\n                \"UNVERIFIED\",\n                \"FIXTURE_ONLY\",\n                \"LIVE_OBSERVED\"\n              ]\n            },\n            \"workspace_read_scope\": {\n              \"enum\": [\n                \"UNVERIFIED\",\n                \"FIXTURE_ONLY\",\n                \"LIVE_OBSERVED\"\n              ]\n            },\n            \"cancellation\": {\n              \"enum\": [\n                \"UNVERIFIED\",\n                \"FIXTURE_ONLY\",\n                \"LIVE_OBSERVED\"\n              ]\n            },\n            \"checked_at\": {\n              \"anyOf\": [\n                {\n                  \"type\": \"string\",\n                  \"format\": \"date-time\"\n                },\n                {\n                  \"type\": \"null\"\n                }\n              ]\n            }\n          },\n          \"required\": [\n            \"execution\",\n            \"workspace_read_scope\",\n            \"cancellation\",\n            \"checked_at\"\n          ]\n        },\n        \"capabilities\": {\n          \"type\": \"object\",\n          \"additionalProperties\": false,\n          \"properties\": {\n            \"readonly_turn\": {\n              \"type\": \"boolean\"\n            },\n            \"event_stream\": {\n              \"type\": \"boolean\"\n            },\n            \"cancel\": {\n              \"type\": \"boolean\"\n            },\n            \"task_history\": {\n              \"type\": \"boolean\"\n            },\n            \"request_lookup\": {\n              \"type\": \"boolean\"\n            },\n            \"token_delta\": {\n              \"const\": false\n            },\n            \"write\": {\n              \"const\": false\n            },\n            \"resume\": {\n              \"const\": false\n            },\n            \"pause\": {\n              \"const\": false\n            },\n            \"per_tool_approval\": {\n              \"const\": false\n            },\n            \"file_diff\": {\n              \"const\": false\n            },\n            \"file_list\": {\n              \"const\": false\n            },\n            \"file_artifacts\": {\n              \"const\": false\n            },\n            \"attachments\": {\n              \"const\": false\n            }\n          },\n          \"required\": [\n            \"readonly_turn\",\n            \"event_stream\",\n            \"cancel\",\n            \"task_history\",\n            \"request_lookup\",\n            \"token_delta\",\n            \"write\",\n            \"resume\",\n            \"pause\",\n            \"per_tool_approval\",\n            \"file_diff\",\n            \"file_list\",\n            \"file_artifacts\",\n            \"attachments\"\n          ]\n        },\n        \"security_scope\": {\n          \"type\": \"object\",\n          \"additionalProperties\": false,\n          \"properties\": {\n            \"mode\": {\n              \"const\": \"workspace-read\"\n            },\n            \"profile_id\": {\n              \"type\": \"string\",\n              \"minLength\": 1,\n              \"maxLength\": 128\n            },\n            \"config_source\": {\n              \"const\": \"HOST_FIXED\"\n            },\n            \"hooks\": {\n              \"const\": \"PLATFORM_POLICY\"\n            },\n            \"mcp\": {\n              \"const\": \"PLATFORM_POLICY\"\n            },\n            \"native_auth\": {\n              \"const\": \"CLI_OWNED\"\n            },\n            \"enforcement_verified\": {\n              \"type\": \"boolean\"\n            }\n          },\n          \"required\": [\n            \"mode\",\n            \"profile_id\",\n            \"config_source\",\n            \"hooks\",\n            \"mcp\",\n            \"native_auth\",\n            \"enforcement_verified\"\n          ]\n        },\n        \"can_submit\": {\n          \"type\": \"boolean\"\n        },\n        \"reason_codes\": {\n          \"type\": \"array\",\n          \"items\": {\n            \"type\": \"string\",\n            \"minLength\": 1,\n            \"maxLength\": 128\n          },\n          \"maxItems\": 16\n        }\n      },\n      \"required\": [\n        \"harness_id\",\n        \"display_name\",\n        \"backend\",\n        \"installation\",\n        \"authentication\",\n        \"verification\",\n        \"capabilities\",\n        \"security_scope\",\n        \"can_submit\",\n        \"reason_codes\"\n      ]\n    },\n    \"Task\": {\n      \"type\": \"object\",\n      \"additionalProperties\": false,\n      \"properties\": {\n        \"task_ref\": {\n          \"$ref\": \"#/$defs/TaskRef\"\n        },\n        \"request_id\": {\n          \"$ref\": \"#/$defs/RequestID\"\n        },\n        \"harness_id\": {\n          \"const\": \"codex\"\n        },\n        \"workspace_ref\": {\n          \"type\": \"string\",\n          \"minLength\": 1,\n          \"maxLength\": 256\n        },\n        \"prompt\": {\n          \"type\": \"string\",\n          \"maxLength\": 65536,\n          \"x-maxUtf8Bytes\": 65536\n        },\n        \"scope\": {\n          \"const\": \"workspace-read\"\n        },\n        \"ephemeral\": {\n          \"const\": true\n        },\n        \"status\": {\n          \"enum\": [\n            \"QUEUED\",\n            \"STARTING\",\n            \"RUNNING\",\n            \"CANCEL_REQUESTED\",\n            \"COMPLETED\",\n            \"FAILED\",\n            \"CANCELLED\",\n            \"BLOCKED\",\n            \"UNKNOWN\"\n          ]\n        },\n        \"terminal\": {\n          \"type\": \"boolean\"\n        },\n        \"task_revision\": {\n          \"$ref\": \"#/$defs/PositiveDecimal\"\n        },\n        \"run\": {\n          \"anyOf\": [\n            {\n              \"$ref\": \"#/$defs/RunRef\"\n            },\n            {\n              \"type\": \"null\"\n            }\n          ]\n        },\n        \"created_at\": {\n          \"type\": \"string\",\n          \"format\": \"date-time\"\n        },\n        \"updated_at\": {\n          \"type\": \"string\",\n          \"format\": \"date-time\"\n        },\n        \"result\": {\n          \"anyOf\": [\n            {\n              \"type\": \"object\",\n              \"additionalProperties\": false,\n              \"properties\": {\n                \"assistant_text\": {\n                  \"type\": \"string\",\n                  \"maxLength\": 1048576,\n                  \"x-maxUtf8Bytes\": 1048576\n                },\n                \"cli_thread_id\": {\n                  \"anyOf\": [\n                    {\n                      \"type\": \"string\",\n                      \"minLength\": 1,\n                      \"maxLength\": 256\n                    },\n                    {\n                      \"type\": \"null\"\n                    }\n                  ]\n                }\n              },\n              \"required\": [\n                \"assistant_text\",\n                \"cli_thread_id\"\n              ]\n            },\n            {\n              \"type\": \"null\"\n            }\n          ]\n        },\n        \"failure\": {\n          \"anyOf\": [\n            {\n              \"$ref\": \"#/$defs/Error\"\n            },\n            {\n              \"type\": \"null\"\n            }\n          ]\n        }\n      },\n      \"required\": [\n        \"task_ref\",\n        \"request_id\",\n        \"harness_id\",\n        \"workspace_ref\",\n        \"prompt\",\n        \"scope\",\n        \"ephemeral\",\n        \"status\",\n        \"terminal\",\n        \"task_revision\",\n        \"run\",\n        \"created_at\",\n        \"updated_at\",\n        \"result\",\n        \"failure\"\n      ]\n    },\n    \"SubmitRequest\": {\n      \"type\": \"object\",\n      \"additionalProperties\": false,\n      \"properties\": {\n        \"request_id\": {\n          \"$ref\": \"#/$defs/RequestID\"\n        },\n        \"project_id\": {\n          \"type\": \"string\",\n          \"minLength\": 1,\n          \"maxLength\": 128\n        },\n        \"workspace_ref\": {\n          \"type\": \"string\",\n          \"minLength\": 1,\n          \"maxLength\": 256\n        },\n        \"harness_id\": {\n          \"const\": \"codex\"\n        },\n        \"scope\": {\n          \"const\": \"workspace-read\"\n        },\n        \"prompt\": {\n          \"type\": \"string\",\n          \"maxLength\": 65536,\n          \"x-maxUtf8Bytes\": 65536\n        }\n      },\n      \"required\": [\n        \"request_id\",\n        \"project_id\",\n        \"workspace_ref\",\n        \"harness_id\",\n        \"scope\",\n        \"prompt\"\n      ]\n    },\n    \"SubmitData\": {\n      \"type\": \"object\",\n      \"additionalProperties\": false,\n      \"properties\": {\n        \"task_ref\": {\n          \"$ref\": \"#/$defs/TaskRef\"\n        },\n        \"request_id\": {\n          \"$ref\": \"#/$defs/RequestID\"\n        },\n        \"task_revision\": {\n          \"$ref\": \"#/$defs/PositiveDecimal\"\n        },\n        \"status\": {\n          \"const\": \"QUEUED\"\n        },\n        \"run\": {\n          \"const\": null\n        }\n      },\n      \"required\": [\n        \"task_ref\",\n        \"request_id\",\n        \"task_revision\",\n        \"status\",\n        \"run\"\n      ]\n    },\n    \"CancelRequest\": {\n      \"type\": \"object\",\n      \"additionalProperties\": false,\n      \"properties\": {\n        \"request_id\": {\n          \"$ref\": \"#/$defs/RequestID\"\n        },\n        \"expected_task_revision\": {\n          \"$ref\": \"#/$defs/PositiveDecimal\"\n        },\n        \"expected_run_id\": {\n          \"anyOf\": [\n            {\n              \"type\": \"string\",\n              \"minLength\": 1,\n              \"maxLength\": 128\n            },\n            {\n              \"type\": \"null\"\n            }\n          ]\n        },\n        \"expected_epoch\": {\n          \"anyOf\": [\n            {\n              \"$ref\": \"#/$defs/PositiveDecimal\"\n            },\n            {\n              \"type\": \"null\"\n            }\n          ]\n        }\n      },\n      \"required\": [\n        \"request_id\",\n        \"expected_task_revision\",\n        \"expected_run_id\",\n        \"expected_epoch\"\n      ]\n    },\n    \"CancelData\": {\n      \"type\": \"object\",\n      \"additionalProperties\": false,\n      \"properties\": {\n        \"task\": {\n          \"$ref\": \"#/$defs/Task\"\n        },\n        \"disposition\": {\n          \"enum\": [\n            \"CANCEL_REQUESTED\",\n            \"CANCELLED_BEFORE_LAUNCH\",\n            \"ALREADY_TERMINAL\"\n          ]\n        }\n      },\n      \"required\": [\n        \"task\",\n        \"disposition\"\n      ]\n    },\n    \"ListData\": {\n      \"type\": \"object\",\n      \"additionalProperties\": false,\n      \"properties\": {\n        \"items\": {\n          \"type\": \"array\",\n          \"items\": {\n            \"$ref\": \"#/$defs/Task\"\n          },\n          \"maxItems\": 100\n        },\n        \"next_cursor\": {\n          \"$ref\": \"#/$defs/Decimal\"\n        },\n        \"has_more\": {\n          \"type\": \"boolean\"\n        },\n        \"lookup\": {\n          \"anyOf\": [\n            {\n              \"type\": \"object\",\n              \"additionalProperties\": false,\n              \"properties\": {\n                \"request_id\": {\n                  \"$ref\": \"#/$defs/RequestID\"\n                },\n                \"state\": {\n                  \"enum\": [\n                    \"FOUND\",\n                    \"NOT_FOUND\"\n                  ]\n                }\n              },\n              \"required\": [\n                \"request_id\",\n                \"state\"\n              ]\n            },\n            {\n              \"type\": \"null\"\n            }\n          ]\n        }\n      },\n      \"required\": [\n        \"items\",\n        \"next_cursor\",\n        \"has_more\",\n        \"lookup\"\n      ]\n    },\n    \"Event\": {\n      \"type\": \"object\",\n      \"additionalProperties\": false,\n      \"properties\": {\n        \"event_id\": {\n          \"type\": \"string\",\n          \"minLength\": 1,\n          \"maxLength\": 128\n        },\n        \"task_ref\": {\n          \"$ref\": \"#/$defs/TaskRef\"\n        },\n        \"run\": {\n          \"anyOf\": [\n            {\n              \"$ref\": \"#/$defs/RunRef\"\n            },\n            {\n              \"type\": \"null\"\n            }\n          ]\n        },\n        \"sequence\": {\n          \"$ref\": \"#/$defs/PositiveDecimal\"\n        },\n        \"timestamp\": {\n          \"type\": \"string\",\n          \"format\": \"date-time\"\n        },\n        \"kind\": {\n          \"enum\": [\n            \"TASK_QUEUED\",\n            \"RUN_STARTED\",\n            \"RUN_STATE\",\n            \"ASSISTANT_MESSAGE\",\n            \"TOOL_EVENT\",\n            \"LOG\",\n            \"TASK_TERMINAL\"\n          ]\n        },\n        \"payload\": {\n          \"type\": \"object\",\n          \"additionalProperties\": false,\n          \"properties\": {\n            \"status\": {\n              \"anyOf\": [\n                {\n                  \"enum\": [\n                    \"QUEUED\",\n                    \"STARTING\",\n                    \"RUNNING\",\n                    \"CANCEL_REQUESTED\",\n                    \"COMPLETED\",\n                    \"FAILED\",\n                    \"CANCELLED\",\n                    \"BLOCKED\",\n                    \"UNKNOWN\"\n                  ]\n                },\n                {\n                  \"type\": \"null\"\n                }\n              ]\n            },\n            \"text\": {\n              \"anyOf\": [\n                {\n                  \"type\": \"string\",\n                  \"maxLength\": 1048576,\n                  \"x-maxUtf8Bytes\": 1048576\n                },\n                {\n                  \"type\": \"null\"\n                }\n              ]\n            },\n            \"tool\": {\n              \"anyOf\": [\n                {\n                  \"type\": \"object\",\n                  \"additionalProperties\": false,\n                  \"properties\": {\n                    \"id\": {\n                      \"type\": \"string\",\n                      \"minLength\": 1,\n                      \"maxLength\": 256\n                    },\n                    \"name\": {\n                      \"type\": \"string\",\n                      \"minLength\": 1,\n                      \"maxLength\": 128\n                    },\n                    \"phase\": {\n                      \"enum\": [\n                        \"STARTED\",\n                        \"COMPLETED\",\n                        \"FAILED\"\n                      ]\n                    },\n                    \"summary\": {\n                      \"type\": \"string\",\n                      \"maxLength\": 4096\n                    }\n                  },\n                  \"required\": [\n                    \"id\",\n                    \"name\",\n                    \"phase\",\n                    \"summary\"\n                  ]\n                },\n                {\n                  \"type\": \"null\"\n                }\n              ]\n            },\n            \"task\": {\n              \"anyOf\": [\n                {\n                  \"$ref\": \"#/$defs/Task\"\n                },\n                {\n                  \"type\": \"null\"\n                }\n              ]\n            },\n            \"error\": {\n              \"anyOf\": [\n                {\n                  \"$ref\": \"#/$defs/Error\"\n                },\n                {\n                  \"type\": \"null\"\n                }\n              ]\n            }\n          },\n          \"required\": [\n            \"status\",\n            \"text\",\n            \"tool\",\n            \"task\",\n            \"error\"\n          ]\n        }\n      },\n      \"required\": [\n        \"event_id\",\n        \"task_ref\",\n        \"run\",\n        \"sequence\",\n        \"timestamp\",\n        \"kind\",\n        \"payload\"\n      ]\n    },\n    \"EventsData\": {\n      \"type\": \"object\",\n      \"additionalProperties\": false,\n      \"properties\": {\n        \"task_ref\": {\n          \"$ref\": \"#/$defs/TaskRef\"\n        },\n        \"events\": {\n          \"type\": \"array\",\n          \"items\": {\n            \"$ref\": \"#/$defs/Event\"\n          },\n          \"maxItems\": 500\n        },\n        \"next_cursor\": {\n          \"$ref\": \"#/$defs/Decimal\"\n        },\n        \"has_more\": {\n          \"type\": \"boolean\"\n        },\n        \"end\": {\n          \"type\": \"boolean\"\n        },\n        \"reset\": {\n          \"type\": \"boolean\"\n        },\n        \"snapshot\": {\n          \"anyOf\": [\n            {\n              \"$ref\": \"#/$defs/Task\"\n            },\n            {\n              \"type\": \"null\"\n            }\n          ]\n        }\n      },\n      \"required\": [\n        \"task_ref\",\n        \"events\",\n        \"next_cursor\",\n        \"has_more\",\n        \"end\",\n        \"reset\",\n        \"snapshot\"\n      ]\n    },\n    \"CapabilitiesResponse\": {\n      \"type\": \"object\",\n      \"additionalProperties\": false,\n      \"properties\": {\n        \"api_version\": {\n          \"const\": \"harness.v1\"\n        },\n        \"data\": {\n          \"$ref\": \"#/$defs/Capabilities\"\n        }\n      },\n      \"required\": [\n        \"api_version\",\n        \"data\"\n      ]\n    },\n    \"SubmitResponse\": {\n      \"type\": \"object\",\n      \"additionalProperties\": false,\n      \"properties\": {\n        \"api_version\": {\n          \"const\": \"harness.v1\"\n        },\n        \"data\": {\n          \"$ref\": \"#/$defs/SubmitData\"\n        }\n      },\n      \"required\": [\n        \"api_version\",\n        \"data\"\n      ]\n    },\n    \"TaskResponse\": {\n      \"type\": \"object\",\n      \"additionalProperties\": false,\n      \"properties\": {\n        \"api_version\": {\n          \"const\": \"harness.v1\"\n        },\n        \"data\": {\n          \"$ref\": \"#/$defs/Task\"\n        }\n      },\n      \"required\": [\n        \"api_version\",\n        \"data\"\n      ]\n    },\n    \"ListResponse\": {\n      \"type\": \"object\",\n      \"additionalProperties\": false,\n      \"properties\": {\n        \"api_version\": {\n          \"const\": \"harness.v1\"\n        },\n        \"data\": {\n          \"$ref\": \"#/$defs/ListData\"\n        }\n      },\n      \"required\": [\n        \"api_version\",\n        \"data\"\n      ]\n    },\n    \"CancelResponse\": {\n      \"type\": \"object\",\n      \"additionalProperties\": false,\n      \"properties\": {\n        \"api_version\": {\n          \"const\": \"harness.v1\"\n        },\n        \"data\": {\n          \"$ref\": \"#/$defs/CancelData\"\n        }\n      },\n      \"required\": [\n        \"api_version\",\n        \"data\"\n      ]\n    },\n    \"EventsResponse\": {\n      \"type\": \"object\",\n      \"additionalProperties\": false,\n      \"properties\": {\n        \"api_version\": {\n          \"const\": \"harness.v1\"\n        },\n        \"data\": {\n          \"$ref\": \"#/$defs/EventsData\"\n        }\n      },\n      \"required\": [\n        \"api_version\",\n        \"data\"\n      ]\n    }\n  },\n  \"identity_and_authority\": [\n    \"Actual Host-issued authenticated principal/native transport context is authoritative. Require current project authorization and principal/project workspace binding. No owner/root/trustedCaller boolean, executable path, argv, auth token or provider endpoint is accepted in a request.\",\n    \"Resolve real workspace and current launch/security policy on the Host. Recheck before launch and on lease/permission change. A capability response or successful metadata probe is not a launch authorization.\",\n    \"Use fixed native Codex executable/version/hash and Host-fixed permission/config arguments. No arbitrary caller command or dangerous bypass. Host-controlled working directory excludes project-local configuration; mandatory native platform policy remains authoritative.\",\n    \"Use default_permissions plus the approved permissions profile; do not combine legacy --sandbox with it. workspace-read is the requested scope, not a proven OS/filesystem isolation claim until independently observed.\",\n    \"Provider authentication remains CLI-owned. Never expose credentials, auth files, raw login output or Core scheduler/executor tokens to UI/CLI child environment.\"\n  ],\n  \"capabilities_rules\": [\n    \"can_submit is computed by Host policy for the requested bounded readonly task. Client cannot assert it. It does not imply execution/model/profile/cancel qualification.\",\n    \"Installation/login metadata and verification are independent. Metadata success must not produce LIVE_OBSERVED or old Mu/model-qualified facts.\",\n    \"readonly_turn/event_stream/cancel/task_history/request_lookup describe implemented operations; verification reports what was actually tested.\",\n    \"token_delta is false in V1: ASSISTANT_MESSAGE is a whole observed message, not fabricated token streaming.\",\n    \"write/resume/pause/per_tool_approval/file_diff/file_list/file_artifacts/attachments are false. UI disables those actions. Do not synthesize a V2 session_id to use old workspace.diff.\",\n    \"can_submit=false must include reason_codes. Unsupported requested functionality is rejected rather than silently ignored.\",\n    \"security_scope.hooks/mcp=PLATFORM_POLICY declares native platform ownership, not proof that extensions are disabled. Fixed flags request optional hooks/plugins disabled; mandatory platform policies are never bypassed. UI must keep verification states separate.\"\n  ],\n  \"submit_and_recovery_rules\": [\n    \"request_id is a stable mutation idempotency key, scoped to actual principal+project+operation. Store exact request hash and original response using existing idempotency storage in the same transaction as Task creation.\",\n    \"Same key/same canonical payload returns the same Task and original response; same key/different payload is409 IDEMPOTENCY_CONFLICT. Replays never create another Task/Run or external launch.\",\n    \"TaskRef is an immutable locator {project_id,task_id}, not a forged domain VersionRef. Task revision and RunRef are separately authoritative.\",\n    \"After a transport timeout/UNKNOWN the renderer must not automatically resubmit or allocate a new request_id. Query GET tasks?project_id=...&request_id=original first.\",\n    \"NOT_FOUND is a read observation, not proof the original request cannot still commit. Keep submission outcome UNKNOWN; allow read-only requery. An explicitly user-requested retry retains the exact original request_id and body.\",\n    \"Run is created only by the sole Coordinator after Task commit. Harness task_type may be harness_turn; it does not require provider/model_config_ref or impersonate mu_turn.\",\n    \"COMPLETED means reconciled native execution with an observed terminal protocol result, not independent business acceptance. No old Goal LIVE gate or formal result is upgraded.\"\n  ],\n  \"cursor_rules\": [\n    \"epoch, task_revision, sequence and every cursor are canonical decimal strings <=9223372036854775807. Cursor/sequence may be0 only where schema allows; epoch/revision/event sequence are positive. Never send JS numeric representations.\",\n    \"Event sequence uses the existing project outbox monotonic sequence; versioned DTO projection is task-scoped. Do not reuse renderer timestamps or duplicate scheduler/event authority.\",\n    \"Recent-task cursor and event cursor are different namespaces despite both being decimal strings; clients keep them separately and reset to0 when project/task changes.\",\n    \"Event cursor is task-specific client state. Pages include only authorized events for the selected Task, with their actual nullable RunRef. next_cursor never moves backwards in an ordinary page.\",\n    \"Persisted event_id/sequence are stable across replay. UI deduplicates and keeps the backend cursor; it does not acknowledge a later cursor before applying that page.\",\n    \"A Run/epoch change does not reset the cursor. RUN_STARTED carries the new RunRef; preserve earlier events as history and use the authoritative current Task for cancel CAS. No automatic resume/relaunch is implied.\",\n    \"Malformed/out-of-int64 cursor returns400 INVALID_REQUEST. A well-formed future/unavailable/pruned cursor returns200 with reset=true, events=[], snapshot=current Task, next_cursor=current authoritative task tail, has_more=false and end=Task.terminal.\",\n    \"On reset the client replaces derived Task state with snapshot and discards its incremental event buffer; it never resubmits work. Poll from next_cursor only when end=false.\",\n    \"For normal pages snapshot=null. end=true only when the Task is terminal AND this page has exhausted the persisted terminal event; a terminal Task with more event pages has end=false.\",\n    \"When no events are returned and no reset is required, preserve cursor. has_more controls immediate next page; otherwise poll with backoff while end=false.\",\n    \"Terminal Task state and its terminal event must commit atomically; do not report end merely from process exit or a non-authoritative cache.\"\n  ],\n  \"cancel_rules\": [\n    \"All CancelRequest fields are required. expected_run_id and expected_epoch must be either both null or both nonnull.\",\n    \"Queued/pre-launch cancellation requires expected_run_id=null,expected_epoch=null and matching expected_task_revision. If Coordinator claimed meanwhile, return409 STATE_CONFLICT; do not cancel the newly observed Run automatically.\",\n    \"Active cancellation requires exact expected_task_revision, expected_run_id and decimal expected_epoch against the actual current Run. Stale/foreign values return409 without affecting another Run.\",\n    \"Cancel is idempotent under its own request_id and exact request hash. An already terminal matching target returns ALREADY_TERMINAL without launch/replay.\",\n    \"CANCEL_REQUESTED acknowledges only durable intent. CANCELLED requires verified child/stream/cleanup terminal facts. Never claim rollback of external effects.\",\n    \"The UI refreshes after STATE_CONFLICT and waits for another explicit user cancel action; it cannot silently substitute a new Run/epoch.\",\n    \"UNKNOWN is not automatic retry or cancellation success. Later read-only reconciliation may refine status without relaunching.\"\n  ],\n  \"event_payload_rules\": {\n    \"TASK_QUEUED\": \"payload.task=current Task; payload.status=QUEUED; run=null.\",\n    \"RUN_STARTED\": \"run=actual new RunRef; payload.status=STARTING or RUNNING.\",\n    \"RUN_STATE\": \"payload.status=current observed lifecycle state.\",\n    \"ASSISTANT_MESSAGE\": \"payload.text=one complete observed assistant message; no synthetic token deltas.\",\n    \"TOOL_EVENT\": \"payload.tool=observed native tool id/name/phase/redacted summary; this is observation, not an approval bridge.\",\n    \"LOG\": \"payload.text=bounded/redacted diagnostic; stderr is never parsed as a success protocol.\",\n    \"TASK_TERMINAL\": \"payload.task=authoritative final Task; payload.status matches; payload.error mirrors failure if any.\",\n    \"all\": \"All five payload keys exist; irrelevant keys are null. No raw secrets, executable argv, auth contents or unbounded tool transcripts are projected.\"\n  },\n  \"task_status_rules\": {\n    \"nonterminal\": [\n      \"QUEUED\",\n      \"STARTING\",\n      \"RUNNING\",\n      \"CANCEL_REQUESTED\"\n    ],\n    \"terminal\": [\n      \"COMPLETED\",\n      \"FAILED\",\n      \"CANCELLED\",\n      \"BLOCKED\",\n      \"UNKNOWN\"\n    ],\n    \"note\": \"Terminal here means no automatic work/relaunch for this V1 request. UNKNOWN may later be refined by existing trusted reconciliation; V1 has no resume operation.\"\n  },\n  \"http_errors\": {\n    \"400\": [\n      \"INVALID_REQUEST\"\n    ],\n    \"401\": [\n      \"HOST_AUTH_REQUIRED\"\n    ],\n    \"403\": [\n      \"FORBIDDEN\",\n      \"WORKSPACE_REVOKED\"\n    ],\n    \"404\": [\n      \"NOT_FOUND\"\n    ],\n    \"409\": [\n      \"STATE_CONFLICT\",\n      \"IDEMPOTENCY_CONFLICT\",\n      \"HARNESS_AUTH_REQUIRED\"\n    ],\n    \"422\": [\n      \"UNSUPPORTED_CAPABILITY\"\n    ],\n    \"500\": [\n      \"INTERNAL_ERROR\"\n    ],\n    \"503\": [\n      \"HARNESS_UNAVAILABLE\"\n    ],\n    \"execution_unknown\": \"Transport uncertainty is initially a client outcome; a persisted execution uncertainty is Task.status UNKNOWN/failure.code EXECUTION_UNKNOWN. Never encode uncertain launch as a fresh retry opportunity.\",\n    \"retryable\": \"Advisory for read-only recovery only. Does not authorize automatic resubmission/cancel retry or a new request_id.\"\n  },\n  \"transport_rules\": [\n    \"Actual Host/native transport authenticates every route. Legacy V2/Mu routes remain compatible and unchanged.\",\n    \"HTTP success response uses {api_version,data}; every failure uses {api_version,error}. No stack traces or raw CLI auth output.\",\n    \"UI/Desktop bridge shares this exact interface. It supplies no authority booleans and preserves decimal strings end to end.\",\n    \"Request prompt is bounded to65536 UTF8 bytes; no attachments in V1. Host controls deadlines/concurrency/output budgets independently of caller.\"\n  ],\n  \"evidence_notes\": [\n    \"Contract source only; not an implementation or runtime qualification.\",\n    \"Current installed Codex metadata/login probe is presence/auth evidence only. Actual model, configured permissions enforcement and cancel/drain behavior remain unverified until the separately registered real path is observed.\",\n    \"No D source or frozen worktree was edited to produce this contract.\",\n    \"D03 revision2: reuse the native Harness under its existing trusted machine/account policy. Actual Windows readonly boundary/events/cancel remain separately unverified; known policy incompatibility or uncontrolled project inheritance blocks only that Run.\"\n  ]\n}\n"
const cliHarnessRoot = "https://researchos.local/cli/harness-v1-rev2"
const cliHarnessReplyLimit = 8 << 20

var cliHarnessID = regexp.MustCompile(`^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$`)

type cliHarnessNoExternal struct{}

func (cliHarnessNoExternal) Load(string) (any, error) {
	return nil, errors.New("external schema resource refused")
}

var cliHarnessSchemas = sync.OnceValues(func() (map[string]*jsonschema.Schema, error) {
	doc, err := domain.Decode([]byte(cliHarnessContract))
	if err != nil {
		return nil, err
	}
	c := jsonschema.NewCompiler()
	c.UseLoader(cliHarnessNoExternal{})
	c.AssertFormat()
	c.DefaultDraft(jsonschema.Draft2020)
	if err = c.AddResource(cliHarnessRoot, doc); err != nil {
		return nil, err
	}
	schemas := map[string]*jsonschema.Schema{}
	for name := range doc["$defs"].(map[string]any) {
		s, err := c.Compile(cliHarnessRoot + "#/$defs/" + name)
		if err != nil {
			return nil, err
		}
		schemas[name] = s
	}
	return schemas, nil
})

type cliHarnessCommand struct {
	operation, project, task, request, workspace, cursor string
	limit                                                int
	submit                                               *domain.HarnessSubmit
	cancel                                               *domain.HarnessCancel
}

func cliHarnessLabel(s string, max int) bool {
	if len(s) == 0 || len(s) > max || !utf8.ValidString(s) || strings.TrimSpace(s) == "" {
		return false
	}
	for _, r := range s {
		if unicode.IsControl(r) {
			return false
		}
	}
	return true
}
func parseCLIHarness(args []string) (cliHarnessCommand, error) {
	var c cliHarnessCommand
	if len(args) == 0 || len(args) == 1 && (args[0] == "help" || args[0] == "--help") {
		c.operation = "help"
		return c, nil
	}
	c.operation = args[0]
	args = args[1:]
	taskNamespace := c.operation == "task"
	if c.operation == "task" {
		if len(args) == 0 {
			return c, errors.New("task action required")
		}
		c.operation = args[0]
		args = args[1:]
	}
	if taskNamespace && c.operation == "caps" || !taskNamespace && c.operation != "caps" {
		return c, errors.New("use caps or task action namespace")
	}
	allowed := map[string]bool{}
	switch c.operation {
	case "caps":
	case "submit":
		for _, k := range []string{"project", "workspace-ref", "request-id", "prompt-stdin"} {
			allowed[k] = true
		}
	case "list":
		for _, k := range []string{"project", "request-id", "cursor", "limit"} {
			allowed[k] = true
		}
	case "get":
		for _, k := range []string{"project", "task"} {
			allowed[k] = true
		}
	case "events":
		for _, k := range []string{"project", "task", "cursor", "limit"} {
			allowed[k] = true
		}
	case "cancel":
		for _, k := range []string{"project", "task", "request-id", "expected-task-revision", "expected-run-id", "expected-epoch", "expect-no-run"} {
			allowed[k] = true
		}
	default:
		return c, errors.New("unsupported Harness action")
	}
	values := map[string]string{}
	for i := 0; i < len(args); i++ {
		token := args[i]
		if !strings.HasPrefix(token, "--") || token == "--" {
			return c, errors.New("named Harness options required")
		}
		name, value, equals := strings.Cut(strings.TrimPrefix(token, "--"), "=")
		if !allowed[name] {
			return c, errors.New("unsupported Harness option")
		}
		if _, exists := values[name]; exists {
			return c, errors.New("duplicate Harness option")
		}
		if name == "prompt-stdin" || name == "expect-no-run" {
			if equals {
				return c, errors.New("flag does not take a value")
			}
			values[name] = "true"
			continue
		}
		if !equals {
			if i+1 >= len(args) || strings.HasPrefix(args[i+1], "--") {
				return c, errors.New("option value required")
			}
			i++
			value = args[i]
		}
		if value == "" {
			return c, errors.New("nonempty option required")
		}
		values[name] = value
	}
	c.project, c.task, c.request, c.workspace = values["project"], values["task"], values["request-id"], values["workspace-ref"]
	if c.operation != "caps" && !cliHarnessLabel(c.project, 128) {
		return c, errors.New("project required")
	}
	if c.operation == "get" || c.operation == "events" || c.operation == "cancel" {
		if !cliHarnessLabel(c.task, 128) {
			return c, errors.New("task required")
		}
	}
	if c.operation == "submit" || c.operation == "cancel" || c.request != "" {
		if !cliHarnessID.MatchString(c.request) {
			return c, errors.New("explicit stable request-id required")
		}
	}
	if c.operation == "submit" {
		if values["prompt-stdin"] != "true" || !cliHarnessLabel(c.workspace, 256) {
			return c, errors.New("workspace-ref and prompt-stdin required")
		}
		c.submit = &domain.HarnessSubmit{RequestID: c.request, ProjectID: c.project, WorkspaceRef: c.workspace, HarnessID: "codex", Scope: "workspace-read"}
	}
	if c.operation == "list" || c.operation == "events" {
		c.cursor = values["cursor"]
		if c.cursor == "" {
			c.cursor = "0"
		}
		if _, err := domain.HarnessDecimal(c.cursor, false); err != nil {
			return c, err
		}
		c.limit = 20
		maximum := 100
		if c.operation == "events" {
			c.limit = 100
			maximum = 500
		}
		if v := values["limit"]; v != "" {
			n, err := strconv.Atoi(v)
			if err != nil || n < 1 || n > maximum || strconv.Itoa(n) != v {
				return c, errors.New("limit outside canonical range")
			}
			c.limit = n
		}
	}
	if c.operation == "cancel" {
		c.cancel = &domain.HarnessCancel{RequestID: c.request, ExpectedTaskRevision: values["expected-task-revision"]}
		run, epoch := values["expected-run-id"], values["expected-epoch"]
		if values["expect-no-run"] == "true" {
			if run != "" || epoch != "" {
				return c, errors.New("queued and active cancel fences conflict")
			}
		} else {
			if run == "" || epoch == "" {
				return c, errors.New("exact run/epoch or expect-no-run required")
			}
			c.cancel.ExpectedRunID = &run
			c.cancel.ExpectedEpoch = &epoch
		}
		if err := c.cancel.Validate(); err != nil {
			return c, err
		}
	}
	return c, nil
}

type cliHarnessHost struct {
	url, id, credential string
	verify              func() error
}
type cliHarnessBoundary struct {
	resolve    func() (resolvedCLIHost, error)
	identity   func(discovery) (string, error)
	credential func(discovery) (string, error)
	native     func(discovery, string, string, map[string]any) (json.RawMessage, error)
}

func currentCLIHarnessHost(ctx context.Context) (*cliHarnessHost, error) {
	return connectCLIHarnessHost(ctx, cliHarnessBoundary{resolveCLIHostDiscovery, cliHostInstanceID, cliSessionCredential, cliNativeRequest})
}
func connectCLIHarnessHost(ctx context.Context, b cliHarnessBoundary) (*cliHarnessHost, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	resolved, err := b.resolve()
	if err != nil {
		return nil, errors.New("Host discovery unavailable")
	}
	d := resolved.discovery
	if !localHostURL(d.URL) || d.DataDir == "" || d.PID <= 0 {
		return nil, errors.New("current local Host required")
	}
	id, err := b.identity(d)
	if err != nil || !cliHostIDPattern.MatchString(id) {
		return nil, errors.New("native Host identity unavailable")
	}
	verify := func() error {
		fresh, err := b.resolve()
		if err != nil || fresh.discovery.URL != d.URL || fresh.discovery.PID != d.PID || !sameHostPath(fresh.discovery.DataDir, d.DataDir) {
			return errors.New("Host identity changed")
		}
		current, err := b.identity(fresh.discovery)
		if err != nil || current != id {
			return errors.New("Host identity changed")
		}
		return nil
	}
	credential, err := b.credential(d)
	if err != nil {
		clientID := "cli-harness-" + domain.ID()
		type outcome struct {
			raw json.RawMessage
			err error
		}
		done := make(chan outcome, 1)
		go func() {
			raw, err := b.native(d, clientID, host.KindUserBootstrapRequest, map[string]any{})
			done <- outcome{raw, err}
		}()
		budget, cancel := context.WithTimeout(ctx, 8*time.Second)
		defer cancel()
		var result outcome
		select {
		case result = <-done:
		case <-budget.Done():
			return nil, errors.New("native Host bootstrap unconfirmed")
		}
		if result.err != nil {
			return nil, errors.New("native Host bootstrap refused")
		}
		var reply struct {
			Principal string `json:"authenticated_principal_ref"`
			Client    string `json:"client_id"`
			Host      string `json:"host_instance_id"`
			Protocol  string `json:"protocol_version"`
			Exposed   bool   `json:"credential_exposed_to_renderer"`
		}
		if cliClosedNativeJSON(result.raw, &reply, "authenticated_principal_ref", "client_id", "host_instance_id", "protocol_version", "credential_exposed_to_renderer") != nil || reply.Principal == "" || reply.Client != clientID || reply.Host != id || reply.Protocol != clientProtocol || reply.Exposed {
			return nil, errors.New("native Host binding invalid")
		}
		credential, err = b.credential(d)
		if err != nil {
			return nil, errors.New("current Host credential unavailable")
		}
	}
	if !cliHarnessLabel(credential, 1024) || verify() != nil {
		return nil, errors.New("current Host credential binding unavailable")
	}
	return &cliHarnessHost{url: strings.TrimSuffix(d.URL, "/"), id: id, credential: credential, verify: verify}, nil
}

type cliHarnessDependencies struct {
	connect   func(context.Context) (*cliHarnessHost, error)
	transport http.RoundTripper
}

func cliHarness(args []string) {
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt)
	defer stop()
	code := runCLIHarness(ctx, args, os.Stdin, os.Stdout, os.Stderr, cliHarnessDependencies{connect: currentCLIHarnessHost})
	os.Exit(code)
}

type cliHarnessExchange struct {
	reply   domain.Object
	http    int
	unknown bool
	reason  string
}

func cliHarnessEndpoint(c cliHarnessCommand) (string, string, any, string) {
	query := url.Values{}
	if c.project != "" {
		query.Set("project_id", c.project)
	}
	path := "/harness/v1/"
	method := "GET"
	var body any
	definition := ""
	switch c.operation {
	case "caps":
		path += "capabilities"
		definition = "CapabilitiesResponse"
	case "submit":
		path += "tasks"
		method = "POST"
		body = c.submit
		definition = "SubmitResponse"
		query = url.Values{}
	case "list":
		path += "tasks"
		query.Set("cursor", c.cursor)
		query.Set("limit", strconv.Itoa(c.limit))
		if c.request != "" {
			query.Set("request_id", c.request)
		}
		definition = "ListResponse"
	case "get":
		path += "tasks/" + url.PathEscape(c.task)
		definition = "TaskResponse"
	case "events":
		path += "tasks/" + url.PathEscape(c.task) + "/events"
		query.Set("cursor", c.cursor)
		query.Set("limit", strconv.Itoa(c.limit))
		definition = "EventsResponse"
	case "cancel":
		path += "tasks/" + url.PathEscape(c.task) + "/cancel"
		method = "POST"
		body = c.cancel
		definition = "CancelResponse"
	}
	if len(query) > 0 {
		path += "?" + query.Encode()
	}
	return method, path, body, definition
}
func cliHarnessCall(ctx context.Context, h *cliHarnessHost, c cliHarnessCommand, transport http.RoundTripper) cliHarnessExchange {
	method, path, body, definition := cliHarnessEndpoint(c)
	if h == nil || h.verify == nil || h.verify() != nil || !localHostURL(h.url) {
		return cliHarnessExchange{reason: "HOST_IDENTITY_CHANGED"}
	}
	if err := ctx.Err(); err != nil {
		return cliHarnessExchange{reason: "INTERRUPTED"}
	}
	raw, err := json.Marshal(body)
	if err != nil {
		return cliHarnessExchange{reason: "REQUEST_INVALID"}
	}
	var reader io.Reader
	if body != nil {
		reader = bytes.NewReader(raw)
	}
	budget, cancel := context.WithTimeout(ctx, 8*time.Second)
	defer cancel()
	request, err := http.NewRequestWithContext(budget, method, h.url+path, reader)
	if err != nil {
		return cliHarnessExchange{reason: "REQUEST_INVALID"}
	}
	request.GetBody = nil // Body request_id is the Core key; HTTP must never replay POST.
	request.Header.Set("Authorization", "Bearer "+h.credential)
	request.Header.Set("Content-Type", "application/json")
	if transport == nil {
		owned := &http.Transport{Proxy: nil, DisableKeepAlives: true}
		defer owned.CloseIdleConnections()
		transport = owned
	}
	client := &http.Client{Transport: transport, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
	response, err := client.Do(request)
	if err != nil {
		return cliHarnessExchange{unknown: method == "POST", reason: "HOST_TRANSPORT_UNCONFIRMED"}
	}
	defer response.Body.Close()
	if response.StatusCode >= 300 && response.StatusCode < 400 {
		return cliHarnessExchange{http: response.StatusCode, unknown: method == "POST", reason: "HOST_REDIRECT_REFUSED"}
	}
	bytes, err := io.ReadAll(io.LimitReader(response.Body, cliHarnessReplyLimit+1))
	if err != nil || len(bytes) > cliHarnessReplyLimit || !utf8.Valid(bytes) || !jsontext.Value(bytes).IsValid() {
		return cliHarnessExchange{http: response.StatusCode, unknown: method == "POST", reason: "HOST_REPLY_UNCONFIRMED"}
	}
	value, err := domain.Decode(bytes)
	if err != nil {
		return cliHarnessExchange{http: response.StatusCode, unknown: method == "POST", reason: "HOST_REPLY_UNCONFIRMED"}
	}
	success := response.StatusCode >= 200 && response.StatusCode < 300
	expected := 200
	if c.operation == "submit" {
		expected = 202
	}
	if success && response.StatusCode != expected {
		return cliHarnessExchange{http: response.StatusCode, unknown: method == "POST", reason: "HOST_STATUS_UNCONFIRMED"}
	}
	name := definition
	if !success {
		name = "ErrorResponse"
	}
	if err = validateCLIHarnessReply(name, value, c); err != nil {
		return cliHarnessExchange{http: response.StatusCode, unknown: method == "POST", reason: "HOST_REPLY_UNCONFIRMED"}
	}
	if !success {
		return cliHarnessExchange{reply: value, http: response.StatusCode, reason: "HOST_REJECTED"}
	}
	return cliHarnessExchange{reply: value, http: response.StatusCode}
}

func cliHarnessDecimals(value any, key string) error {
	if key == "epoch" || key == "sequence" || key == "next_cursor" || key == "task_revision" || key == "current_task_revision" {
		if value != nil {
			s, ok := value.(string)
			if !ok {
				return errors.New("wire decimal must be string")
			}
			if _, err := domain.HarnessDecimal(s, key != "next_cursor"); err != nil {
				return err
			}
		}
	}
	if key == "prompt" {
		if s, ok := value.(string); ok && len(s) > 65536 {
			return errors.New("prompt UTF8 byte bound exceeded")
		}
	}
	if key == "assistant_text" || key == "text" {
		if s, ok := value.(string); ok && len(s) > 1<<20 {
			return errors.New("text UTF8 byte bound exceeded")
		}
	}
	switch v := value.(type) {
	case map[string]any:
		for k, item := range v {
			if err := cliHarnessDecimals(item, k); err != nil {
				return err
			}
		}
	case []any:
		for _, item := range v {
			if err := cliHarnessDecimals(item, ""); err != nil {
				return err
			}
		}
	}
	return nil
}
func cliHarnessTask(value any, project, task string) error {
	v, ok := value.(map[string]any)
	if !ok {
		return errors.New("task required")
	}
	ref := v["task_ref"].(map[string]any)
	if ref["project_id"] != project || task != "" && ref["task_id"] != task {
		return errors.New("task reference changed")
	}
	terminal := false
	switch v["status"] {
	case "COMPLETED", "FAILED", "CANCELLED", "BLOCKED", "UNKNOWN":
		terminal = true
	}
	if v["terminal"] != terminal {
		return errors.New("task terminal state differs")
	}
	return nil
}
func validateCLIHarnessReply(definition string, value domain.Object, c cliHarnessCommand) error {
	schemas, err := cliHarnessSchemas()
	if err != nil {
		return err
	}
	s := schemas[definition]
	if s == nil {
		return errors.New("unknown response definition")
	}
	if err = s.Validate(value); err != nil {
		return err
	}
	if err = cliHarnessDecimals(value, ""); err != nil {
		return err
	}
	if definition == "ErrorResponse" {
		e := value["error"].(map[string]any)
		if ref, ok := e["task_ref"].(map[string]any); ok && (ref["project_id"] != c.project || c.task != "" && ref["task_id"] != c.task) {
			return errors.New("error task reference changed")
		}
		return nil
	}
	data := value["data"].(map[string]any)
	switch definition {
	case "CapabilitiesResponse":
		if data["can_submit"] == false && len(data["reason_codes"].([]any)) == 0 {
			return errors.New("unavailable capability needs reason")
		}
	case "SubmitResponse":
		ref := data["task_ref"].(map[string]any)
		if ref["project_id"] != c.project || data["request_id"] != c.request {
			return errors.New("submit acknowledgement changed")
		}
	case "TaskResponse":
		return cliHarnessTask(data, c.project, c.task)
	case "CancelResponse":
		task := data["task"].(map[string]any)
		if err = cliHarnessTask(task, c.project, c.task); err != nil {
			return err
		}
		switch data["disposition"] {
		case "CANCEL_REQUESTED":
			if task["status"] != "CANCEL_REQUESTED" || task["terminal"] != false {
				return errors.New("cancel not requested")
			}
		case "CANCELLED_BEFORE_LAUNCH":
			if task["status"] != "CANCELLED" || task["run"] != nil {
				return errors.New("queued cancellation differs")
			}
		case "ALREADY_TERMINAL":
			if task["terminal"] != true {
				return errors.New("cancel terminal claim differs")
			}
		}
		if c.cancel == nil {
			return errors.New("cancel fence missing")
		}
		if c.cancel.ExpectedRunID != nil {
			ref, ok := task["run"].(map[string]any)
			if !ok || ref["run_id"] != *c.cancel.ExpectedRunID || ref["epoch"] != *c.cancel.ExpectedEpoch {
				return errors.New("cancel acknowledged a different Run")
			}
		} else if task["run"] != nil {
			return errors.New("queued cancel acknowledged a claimed Run")
		}
	case "ListResponse":
		seen := map[string]bool{}
		items := data["items"].([]any)
		if len(items) > c.limit {
			return errors.New("list exceeds requested limit")
		}
		if c.request == "" {
			if data["lookup"] != nil {
				return errors.New("unexpected request lookup")
			}
			next, _ := domain.HarnessDecimal(data["next_cursor"].(string), false)
			cursor, _ := domain.HarnessDecimal(c.cursor, false)
			if len(items) == 0 && next != cursor || len(items) > 0 && (next == 0 || cursor > 0 && next >= cursor) {
				return errors.New("list cursor differs")
			}
		}
		for _, item := range items {
			if err = cliHarnessTask(item, c.project, ""); err != nil {
				return err
			}
			t := item.(map[string]any)
			id := t["task_ref"].(map[string]any)["task_id"].(string)
			if seen[id] {
				return errors.New("duplicate task")
			}
			seen[id] = true
		}
		if c.request != "" {
			lookup, ok := data["lookup"].(map[string]any)
			if !ok || lookup["request_id"] != c.request {
				return errors.New("lookup key differs")
			}
			switch lookup["state"] {
			case "FOUND":
				if len(items) != 1 || items[0].(map[string]any)["request_id"] != c.request {
					return errors.New("lookup result differs")
				}
			case "NOT_FOUND":
				if len(items) != 0 {
					return errors.New("missing lookup has items")
				}
			}
		}
	case "EventsResponse":
		return validateCLIHarnessEvents(data, c)
	}
	return nil
}
func validateCLIHarnessEvents(data domain.Object, c cliHarnessCommand) error {
	same := func(ref any) bool {
		r, ok := ref.(map[string]any)
		return ok && r["project_id"] == c.project && r["task_id"] == c.task
	}
	if !same(data["task_ref"]) {
		return errors.New("event task changed")
	}
	events := data["events"].([]any)
	next, _ := domain.HarnessDecimal(data["next_cursor"].(string), false)
	cursor, _ := domain.HarnessDecimal(c.cursor, false)
	if data["reset"] == true {
		if len(events) != 0 || data["has_more"] != false || data["snapshot"] == nil {
			return errors.New("invalid reset")
		}
		if err := cliHarnessTask(data["snapshot"], c.project, c.task); err != nil {
			return err
		}
		if data["end"] != data["snapshot"].(map[string]any)["terminal"] {
			return errors.New("reset terminal differs")
		}
		return nil
	}
	if data["snapshot"] != nil || next < cursor || data["end"] == true && data["has_more"] == true || len(events) == 0 && next != cursor {
		return errors.New("invalid event page")
	}
	seen := map[string]bool{}
	previous := cursor
	for _, item := range events {
		event := item.(map[string]any)
		if !same(event["task_ref"]) {
			return errors.New("event reference differs")
		}
		id := event["event_id"].(string)
		seq, _ := domain.HarnessDecimal(event["sequence"].(string), true)
		if seen[id] || seq <= previous || seq > next {
			return errors.New("event order differs")
		}
		seen[id] = true
		previous = seq
		p := event["payload"].(map[string]any)
		kind := event["kind"]
		if p["task"] != nil {
			if err := cliHarnessTask(p["task"], c.project, c.task); err != nil {
				return err
			}
			t := p["task"].(map[string]any)
			if p["status"] != t["status"] || domain.Hash(t["run"]) != domain.Hash(event["run"]) {
				return errors.New("event snapshot differs")
			}
		}
		switch kind {
		case "TASK_QUEUED":
			if event["run"] != nil || p["status"] != "QUEUED" || p["task"] == nil || p["text"] != nil || p["tool"] != nil || p["error"] != nil {
				return errors.New("invalid queued event")
			}
		case "RUN_STARTED":
			if event["run"] == nil || p["status"] != "STARTING" && p["status"] != "RUNNING" || p["text"] != nil || p["tool"] != nil || p["error"] != nil {
				return errors.New("invalid started event")
			}
		case "RUN_STATE":
			if event["run"] == nil || p["status"] == nil || p["task"] != nil || p["text"] != nil || p["tool"] != nil || p["error"] != nil {
				return errors.New("invalid run state event")
			}
		case "TASK_TERMINAL":
			if p["task"] == nil || p["task"].(map[string]any)["terminal"] != true || domain.Hash(p["error"]) != domain.Hash(p["task"].(map[string]any)["failure"]) || p["text"] != nil || p["tool"] != nil {
				return errors.New("invalid terminal event")
			}
		case "ASSISTANT_MESSAGE", "LOG":
			if p["text"] == nil || p["status"] != nil || p["task"] != nil || p["tool"] != nil || p["error"] != nil {
				return errors.New("invalid text event")
			}
		case "TOOL_EVENT":
			if p["tool"] == nil || p["status"] != nil || p["task"] != nil || p["text"] != nil || p["error"] != nil {
				return errors.New("invalid tool event")
			}
		}
	}
	if len(events) > 0 && previous != next {
		return errors.New("event cursor differs from tail")
	}
	return nil
}

func runCLIHarness(ctx context.Context, args []string, input io.Reader, output, diagnostic io.Writer, deps cliHarnessDependencies) int {
	command, err := parseCLIHarness(args)
	report := domain.Object{"command": "harness", "status": "REJECTED", "exit_code": exitUsage}
	credential := ""
	emit := func(code int) int {
		report["exit_code"] = code
		raw, err := json.Marshal(cliHarnessSafeOutput(report, credential))
		if err != nil {
			return exitFailed
		}
		raw = rt.Redact(raw)
		if _, err = fmt.Fprintln(output, string(raw)); err != nil {
			return exitFailed
		}
		return code
	}
	if err != nil {
		report["reason"] = "INVALID_REQUEST"
		fmt.Fprintln(diagnostic, "harness: invalid options; use researchos harness help")
		return emit(exitUsage)
	}
	report["command"] = "harness " + command.operation
	if command.operation == "help" {
		report["status"] = "COMPLETED"
		report["completion_scope"] = "USAGE"
		report["usage"] = []string{"researchos harness caps", "researchos harness task submit --project P --workspace-ref W --request-id K --prompt-stdin", "researchos harness task list --project P [--request-id K] [--cursor C] [--limit N]", "researchos harness task get --project P --task T", "researchos harness task events --project P --task T [--cursor C] [--limit N]", "researchos harness task cancel --project P --task T --request-id CK --expected-task-revision R --expect-no-run", "researchos harness task cancel --project P --task T --request-id CK --expected-task-revision R --expected-run-id RUN --expected-epoch E"}
		return emit(exitCompleted)
	}
	report["project_id"], report["request_id"], report["task_id"] = command.project, command.request, command.task
	if command.submit != nil {
		prompt, problem := readCLIHarnessPrompt(ctx, input)
		if problem != nil {
			report["reason"] = problem.reason
			return emit(problem.code)
		}
		if strings.ContainsRune(prompt, 0) {
			report["reason"] = "PROMPT_INVALID"
			return emit(exitUsage)
		}
		command.submit.Prompt = prompt
		if command.submit.Validate() != nil {
			report["reason"] = "PROMPT_INVALID"
			return emit(exitUsage)
		}
	}
	if ctx.Err() != nil {
		report["reason"] = "INTERRUPTED"
		return emit(exitInterrupted)
	}
	if deps.connect == nil {
		report["reason"] = "HOST_UNAVAILABLE"
		return emit(exitNotImplemented)
	}
	h, err := deps.connect(ctx)
	if err != nil || h == nil {
		if ctx.Err() != nil {
			report["reason"] = "INTERRUPTED"
			return emit(exitInterrupted)
		}
		report["reason"] = "HOST_AUTH_REQUIRED"
		return emit(exitNotImplemented)
	}
	credential = h.credential
	exchange := cliHarnessCall(ctx, h, command, deps.transport)
	if exchange.unknown {
		report["status"] = "UNKNOWN"
		report["reason"] = exchange.reason
		lookup := cliHarnessCommand{operation: "list", project: command.project, request: command.request, cursor: "0", limit: 1}
		if command.operation == "cancel" {
			lookup = cliHarnessCommand{operation: "get", project: command.project, task: command.task}
		}
		observed := cliHarnessCall(ctx, h, lookup, deps.transport)
		if observed.reason == "" {
			report["observation"] = observed.reply
			if command.submit != nil {
				data := observed.reply["data"].(map[string]any)
				items := data["items"].([]any)
				if len(items) == 1 {
					task := items[0].(map[string]any)
					if task["workspace_ref"] == command.workspace && task["prompt"] == command.submit.Prompt && task["harness_id"] == "codex" && task["scope"] == "workspace-read" {
						report["status"] = "ACKNOWLEDGED"
						report["completion_scope"] = "SUBMIT_REQUEST_LOOKUP"
						report["task_id"] = task["task_ref"].(map[string]any)["task_id"]
						return emit(exitCompleted)
					}
				}
			}
		}
		report["recovery"] = "Read the original request/task through the same Host; do not automatically POST again."
		return emit(exitFailed)
	}
	if exchange.reason != "" {
		report["reason"] = exchange.reason
		if exchange.reply != nil {
			report["response"] = exchange.reply
		}
		if ctx.Err() != nil {
			return emit(exitInterrupted)
		}
		if exchange.http == 400 {
			return emit(exitUsage)
		}
		if exchange.http >= 400 && exchange.http < 500 {
			return emit(exitNotImplemented)
		}
		return emit(exitFailed)
	}
	report["response"] = exchange.reply
	if command.submit != nil || command.cancel != nil {
		report["status"] = "ACKNOWLEDGED"
		report["completion_scope"] = "HOST_MUTATION_ACK"
	} else {
		report["status"] = "COMPLETED"
		report["completion_scope"] = "HOST_QUERY"
	}
	return emit(exitCompleted)
}

func cliHarnessSafeOutput(value any, credential string) any {
	switch v := value.(type) {
	case string:
		if credential != "" {
			return strings.ReplaceAll(v, credential, "[REDACTED]")
		}
		return v
	case map[string]any:
		copy := map[string]any{}
		for k, item := range v {
			copy[k] = cliHarnessSafeOutput(item, credential)
		}
		return copy
	case []any:
		copy := make([]any, len(v))
		for i, item := range v {
			copy[i] = cliHarnessSafeOutput(item, credential)
		}
		return copy
	default:
		return value
	}
}

func readCLIHarnessPrompt(ctx context.Context, input io.Reader) (string, *cliPromptProblem) {
	interrupted := func() (string, *cliPromptProblem) {
		return "", &cliPromptProblem{code: exitInterrupted, reason: "INTERRUPTED", detail: "stdin read interrupted before Host request"}
	}
	if ctx.Err() != nil {
		return interrupted()
	}
	if input == nil {
		return "", &cliPromptProblem{code: exitFailed, reason: "PROMPT_UNREADABLE", detail: "stdin unavailable"}
	}
	type result struct {
		text    string
		problem *cliPromptProblem
	}
	done := make(chan result, 1)
	go func() { text, problem := readCLIPrompt(input); done <- result{text, problem} }()
	select {
	case value := <-done:
		if ctx.Err() != nil {
			return interrupted()
		}
		return value.text, value.problem
	case <-ctx.Done():
		if closer, ok := input.(io.Closer); ok {
			_ = closer.Close()
		}
		return interrupted()
	}
}
