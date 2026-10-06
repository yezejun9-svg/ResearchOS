package canonical

import "testing"

func TestJSON(t *testing.T) {
	// U+1E30 sorts before this non-BMP key in both UTF-16 and code point order.
	got, err := JSON([]byte(`{"😀":1,"Ḱ":2,"z":1e-7,"n":-0,"a":"é"}`))
	if err != nil {
		t.Fatal(err)
	}
	want := `{"a":"é","n":0,"z":1e-7,"Ḱ":2,"😀":1}`
	if string(got) != want {
		t.Fatalf("canonical JSON = %s, want %s", got, want)
	}
	for _, input := range []string{`{"a":1,"a":2}`, `{"a":1,"\u0061":2}`, `{"a":NaN}`, `{"a":Infinity}`, `{"a":"\ud800"}`, `1e999`} {
		if got, err := JSON([]byte(input)); err == nil {
			t.Errorf("accepted invalid JCS input %q as %q", input, got)
		}
	}
}

func TestUTF16AndFieldOrder(t *testing.T) {
	// UTF-16 orders U+10000 (D800 DC00) before U+E000; code point order is the opposite.
	want := "{\"𐀀\":2,\"\ue000\":1}"
	for _, input := range []string{"{\"\ue000\":1,\"𐀀\":2}", "{\"𐀀\":2,\"\ue000\":1}"} {
		got, err := JSON([]byte(input))
		if err != nil || string(got) != want {
			t.Fatalf("UTF-16 JCS: %s %v", got, err)
		}
	}
}
