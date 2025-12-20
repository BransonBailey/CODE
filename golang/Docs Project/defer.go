package main

import (
    "fmt"
    "os"
    "path/filepath"
)

func main() {

    path := filepath.Join(os.TempDir(), "defer.txt")
    f := createFile(path)
    defer closeFile(f)
    writeFile(f)
}

func createFile(p string) *os.File {
    fmt.Println("creating")
    f, err := os.Create(p)
    if err != nil {
        panic(err)
    }
    return f
}

func writeFile(f *os.File) {
    fmt.Println("writing")
    fmt.Fprintln(f, "data")
}

func closeFile(f *os.File) {
    fmt.Println("closing")
    err := f.Close()

    if err != nil {
        panic(err)
    }
}
