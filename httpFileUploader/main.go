package main

import (
	"fmt"
	"io"
	"net/http"
	"os"
	"text/template"
	"time"
)

// Compile templates on start of the application
var templates = template.Must(template.ParseFiles("public/upload.html"))

// Display the named template
func display(w http.ResponseWriter, page string, data interface{}) {
	templates.ExecuteTemplate(w, page+".html", data)
}

func uploadFile(w http.ResponseWriter, r *http.Request) {

	t1 := time.Now()
	nowTimeStr := fmt.Sprintf("%s", t1.Format(time.RFC3339))
	bgnStr := fmt.Sprintf("%s upload request from : %+v", nowTimeStr, r.RemoteAddr)
	// Maximum upload of 10 MB files
	// fmt.Printf("%s ...", bgnStr)
	r.ParseMultipartForm(10 << 20)

	//fmt.Printf("requester RemoteAddr: %+v\n", r.RemoteAddr)

	// Get handler for filename, size and headers
	file, handler, err := r.FormFile("myFile")
	if err != nil {
		fmt.Printf("Error Retrieving the File from %+v\n /w error %+v\n",r.RemoteAddr,err)
		//fmt.Println(err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	defer file.Close()
	//fmt.Printf("Uploaded File: %+v\n", handler.Filename)
	//fmt.Printf("File Size: %+v\n", handler.Size)
	//fmt.Printf("MIME Header: %+v\n", handler.Header)

	t2 := time.Now()
	doneTimeStr := fmt.Sprintf("%s", t2.Format(time.RFC3339))
	fmt.Printf("%s,%+vBytes, done at %v time cost: %v\n", bgnStr, handler.Size,doneTimeStr, t2.Sub(t1))

	// Create file
	// outFilFullPath := fmt.Sprintf("/go/uploaded/%s",handler.Filename)
	dst, err := os.Create(handler.Filename)
	defer dst.Close()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// Copy the uploaded file to the created file on the filesystem
	if _, err := io.Copy(dst, file); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	//fmt.Fprintf(w, "Successfully Uploaded File\n-------------------------------\n")
}

func uploadHandler(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case "GET":
		display(w, "upload", nil)
	case "POST":
		uploadFile(w, r)
	}
}

func main() {
	// Upload route
	http.HandleFunc("/upload", uploadHandler)

	//Listen on port 8080
	http.ListenAndServe(":8080", nil)
}
