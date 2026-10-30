export type DialogueState =
  | 'GREETING'
  | 'COLLECTING_SLOTS'
  | 'CLARIFYING'
  | 'CONFIRMING'
  | 'EVALUATION_READY'
  | 'RESPONDING'
  | 'COMPLETED'
  | 'PAUSED';

export interface SlotFact {
  slot_key: string;
  canonical_value: any;
  canonical_unit?: string | null;
  status: string;
  provenance: string;
}

export interface ConversationTurnDTO {
  turn_number: number;
  role: 'FARMER' | 'ASSISTANT' | 'SYSTEM_EVENT';
  input_mode: 'VOICE' | 'TEXT' | 'NONE';
  transcript_text?: string | null;
  assistant_text?: string | null;
  audio_url?: string | null;
  created_at: string;
}

export interface ConversationResponse {
  conversation_id: string;
  farmer_id: string;
  status: 'ACTIVE' | 'PAUSED' | 'COMPLETED' | 'DELETED';
  state: DialogueState;
  language: string;
  current_intent?: string | null;
  summary?: string | null;
  profile?: Record<string, any> | null;
  missing_slots: string[];
  slots?: SlotFact[];
  version: number;
  created_at: string;
  last_activity_at?: string | null;
}

export interface TurnResponse {
  turn_id: string;
  turn_number: number;
  conversation_id: string;
  dialogue_state: DialogueState;
  transcript_text: string;
  assistant_text: string;
  audio_url?: string | null;
  speech_available: boolean;
  missing_slots: string[];
  next_required_slot?: string | null;
  is_ready_for_evaluation: boolean;
  conflicts: string[];
  extracted_intent?: string | null;
  version: number;
}

export interface TurnTextRequest {
  text: string;
  language?: string;
  client_turn_id?: string | null;
  expected_version?: number | null;
}
