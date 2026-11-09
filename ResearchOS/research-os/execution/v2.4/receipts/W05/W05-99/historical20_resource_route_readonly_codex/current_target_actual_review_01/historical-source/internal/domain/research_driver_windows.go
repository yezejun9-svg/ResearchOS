//go:build windows

package domain

import (
	"context"
	"errors"
	"time"
)

func (c *RuntimeCoordinator) advanceResearchCycles(ctx context.Context) error {
	rows, err := c.service.DB.QueryContext(ctx, "SELECT project FROM intent_plan_bindings WHERE monitor_current=1 ORDER BY project")
	if err != nil {
		return err
	}
	projects := []string{}
	for rows.Next() {
		var project string
		if err = rows.Scan(&project); err != nil {
			rows.Close()
			return err
		}
		projects = append(projects, project)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return err
	}
	failures := []error{}
	for _, project := range projects {
		tx, err := c.service.DB.BeginTx(ctx, nil)
		if err != nil {
			failures = append(failures, err)
			continue
		}
		if err = resourceWriteLock(tx); err == nil {
			p, e := resourcePrincipal(tx, c.config.SchedulerToken, project, "SCHEDULER")
			if e != nil {
				err = e
			} else {
				err = c.service.advanceResearchProject(tx, p, project, time.Now().UTC())
			}
		}
		if err == nil {
			err = tx.Commit()
		}
		tx.Rollback()
		if err != nil {
			failures = append(failures, err)
		}
	}
	return errors.Join(failures...)
}
