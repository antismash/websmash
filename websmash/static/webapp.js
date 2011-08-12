function addFileInfo() {
    var name = document.getElementById('seq').value;
    var cleaned_name = name.replace(/\\/g, "/");
    var basename = cleaned_name.split('/').pop();
    document.getElementById('seq_name').value = basename;
}
