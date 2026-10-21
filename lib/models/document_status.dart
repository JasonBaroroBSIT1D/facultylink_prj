enum DocumentStatus {
  fileSelected,
  uploading,
  ocrProcessing,
  classifying,
  validating,
  systemApproved,
  needsVerification,
  needsRevision,
  rejected,
  uploadFailed,
}

extension DocumentStatusLabel on DocumentStatus {
  String get label {
    switch (this) {
      case DocumentStatus.fileSelected:
        return 'File Selected';
      case DocumentStatus.uploading:
        return 'Uploading';
      case DocumentStatus.ocrProcessing:
        return 'OCR Processing';
      case DocumentStatus.classifying:
        return 'Classifying';
      case DocumentStatus.validating:
        return 'Rule-Based Validation';
      case DocumentStatus.systemApproved:
        return 'System Approved';
      case DocumentStatus.needsVerification:
        return 'Needs Verification';
      case DocumentStatus.needsRevision:
        return 'Needs Revision';
      case DocumentStatus.rejected:
        return 'Rejected';
      case DocumentStatus.uploadFailed:
        return 'Upload Failed';
    }
  }
}
