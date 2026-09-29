package canonical

import "testing"

func TestJSON(t *testing.T) {
	// RFC 8785 key order follows UTF-16; 1E30 sorts before the non-BMP key.
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
