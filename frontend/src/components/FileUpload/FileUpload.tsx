import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';

interface FileUploadProps {
  onFilesSelected: (files: File[]) => void;
  maxFileSize?: number; // in bytes
  maxFiles?: number;
  acceptedFormats?: string[];
}

interface UploadFile {
  file: File;
  id: string;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
  error?: string;
}

const FileUpload: React.FC<FileUploadProps> = ({
  onFilesSelected,
  maxFileSize = 50 * 1024 * 1024, // 50MB default as per Issue #6
  maxFiles = 100, // Batch limit from Issue #6
  acceptedFormats = ['.pdf', '.docx', '.doc', '.txt', '.rtf'] // Formats from Issue #6
}) => {
  const [uploadQueue, setUploadQueue] = useState<UploadFile[]>([]);
  const [isDragActive, setIsDragActive] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    // Validate files
    const validFiles = acceptedFiles.filter(file => {
      if (file.size > maxFileSize) {
        console.error(`File ${file.name} exceeds max size of ${maxFileSize / 1024 / 1024}MB`);
        return false;
      }
      return true;
    });

    if (validFiles.length > 0) {
      const newUploadFiles: UploadFile[] = validFiles.map(file => ({
        file,
        id: `${file.name}-${Date.now()}-${Math.random()}`,
        status: 'pending',
        progress: 0
      }));

      setUploadQueue(prev => [...prev, ...newUploadFiles]);
      onFilesSelected(validFiles);
    }

    // Handle rejected files
    rejectedFiles.forEach(rejection => {
      console.error(`File ${rejection.file.name} rejected:`, rejection.errors);
    });
  }, [maxFileSize, onFilesSelected]);

  const { getRootProps, getInputProps } = useDropzone({
    onDrop,
    accept: acceptedFormats.reduce((acc, format) => {
      // Map file extensions to MIME types
      const mimeTypes: { [key: string]: string[] } = {
        '.pdf': ['application/pdf'],
        '.docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
        '.doc': ['application/msword'],
        '.txt': ['text/plain'],
        '.rtf': ['application/rtf', 'text/rtf']
      };
      
      if (mimeTypes[format]) {
        acc[format] = mimeTypes[format];
      }
      return acc;
    }, {} as { [key: string]: string[] }),
    maxFiles,
    maxSize: maxFileSize,
    onDragEnter: () => setIsDragActive(true),
    onDragLeave: () => setIsDragActive(false),
    onDropAccepted: () => setIsDragActive(false),
    onDropRejected: () => setIsDragActive(false)
  });

  const removeFile = (fileId: string) => {
    setUploadQueue(prev => prev.filter(f => f.id !== fileId));
  };

  const getStatusIcon = (status: UploadFile['status']) => {
    switch (status) {
      case 'pending': return '⏳';
      case 'uploading': return '📤';
      case 'processing': return '⚙️';
      case 'completed': return '✅';
      case 'error': return '❌';
      default: return '📄';
    }
  };

  return (
    <div className="w-full">
      {/* Upload Zone - Following Issue #6 design */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
          transition-all duration-200 ease-in-out
          ${isDragActive 
            ? 'border-blue-500 bg-blue-50 scale-102' 
            : 'border-gray-300 hover:border-gray-400'
          }
        `}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center space-y-4">
          <div className="text-5xl">📄</div>
          <div className="text-lg font-medium text-gray-700">
            {isDragActive
              ? 'Drop files here...'
              : 'Drop PDFs here or click to browse'
            }
          </div>
          <div className="text-sm text-gray-500">
            Supported formats: {acceptedFormats.join(', ')}
          </div>
          <div className="text-xs text-gray-400">
            Max file size: {maxFileSize / 1024 / 1024}MB • Max files: {maxFiles}
          </div>
        </div>
      </div>

      {/* Processing Queue - Following Issue #6 design */}
      {uploadQueue.length > 0 && (
        <div className="mt-6">
          <h3 className="text-lg font-semibold mb-3">Processing Queue:</h3>
          <div className="space-y-2">
            {uploadQueue.map(uploadFile => (
              <div
                key={uploadFile.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center space-x-3 flex-1">
                  <span className="text-xl">{getStatusIcon(uploadFile.status)}</span>
                  <div className="flex-1">
                    <div className="font-medium text-sm truncate max-w-md">
                      {uploadFile.file.name}
                    </div>
                    {uploadFile.status === 'uploading' || uploadFile.status === 'processing' ? (
                      <div className="mt-1">
                        <div className="text-xs text-gray-500 mb-1">
                          {uploadFile.progress}%
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-1.5">
                          <div
                            className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                            style={{ width: `${uploadFile.progress}%` }}
                          />
                        </div>
                      </div>
                    ) : uploadFile.status === 'completed' ? (
                      <div className="text-xs text-green-600">Complete</div>
                    ) : uploadFile.status === 'error' ? (
                      <div className="text-xs text-red-600">
                        Error: {uploadFile.error || 'Failed to process'}
                      </div>
                    ) : (
                      <div className="text-xs text-gray-500">Waiting...</div>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => removeFile(uploadFile.id)}
                  className="ml-3 text-gray-400 hover:text-gray-600"
                  title="Remove"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUpload;