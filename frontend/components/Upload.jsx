import React, { useState } from "react";

export default function Upload({ onUpload }) {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");

  const handleUpload = async () => {
    if (!file) {
      setStatus("Please choose a file first.");
      return;
    }
    setStatus("Uploading...");
    const result = await onUpload(file);
    setStatus(
      result?.status === "success"
        ? `Indexed ${result.data.chunks_created} chunks.`
        : `Error: ${result?.message || "upload failed"}`
    );
  };

  return (
    <div className="upload-box">
      <input type="file" onChange={(e) => setFile(e.target.files[0])} />
      <button onClick={handleUpload}>Upload</button>
      <p>{status}</p>
    </div>
  );
}
