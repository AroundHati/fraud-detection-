export type ClaimStatus =
  | "uploaded"
  | "processing"
  | "investigating"
  | "completed";

export type Claim = {
  id: string;
  uploaded_by: string;
  patient_id: string;
  patient_name: string;
  provider_id: string;
  provider_name: string;
  claim_amount: number;
  diagnosis_codes: string[];
  procedure_codes: string[];
  claim_date: string;
  status: ClaimStatus;
  fraud_probability: number | null;
  created_at: string;
  updated_at: string;
};

export type ClaimFormData = {
  patient_id: string;
  patient_name: string;
  provider_id: string;
  provider_name: string;
  claim_amount: number;
  diagnosis_codes: string[];
  procedure_codes: string[];
  claim_date: string;
};

export type ClaimUploadFile = {
  file: File;
  document_type:
    | "claim"
    | "prescription"
    | "discharge_summary"
    | "medical_bill"
    | "doctor_note";
};
