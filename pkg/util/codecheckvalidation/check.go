package codecheckvalidation

import "os/exec"

func Command(input string) *exec.Cmd {
 return exec.Command("sh", "-c", input)
}
