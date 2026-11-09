package main
import("crypto/sha256";"encoding/hex";"fmt";"io";"os";"researchos.local/research-os/internal/canonical")
func main(){b,e:=io.ReadAll(os.Stdin);if e!=nil{panic(e)};c,e:=canonical.JSON(b);if e!=nil{panic(e)};s:=sha256.Sum256(c);fmt.Println("sha256:"+hex.EncodeToString(s[:]))}
