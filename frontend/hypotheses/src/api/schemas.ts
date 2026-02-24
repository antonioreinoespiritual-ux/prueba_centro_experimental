import { z } from 'zod';

export const experimentSchema = z.object({
  id: z.number(),
  project_name: z.string(),
  hypothesis: z.string().nullable().optional(),
  traffic_type: z.string().nullable().optional(),
  created_at: z.string().nullable().optional(),
  updated_at: z.string().nullable().optional(),
  drive_folder_path: z.string().nullable().optional(),
  hypothesis_type: z.string().nullable().optional(),
  independent_variable: z.string().nullable().optional(),
  metric_x: z.string().nullable().optional(),
  primary_metric: z.string().nullable().optional(),
  validation_threshold: z.string().nullable().optional(),
  threshold_value: z.number().nullable().optional(),
  threshold_type: z.string().nullable().optional(),
  threshold_operator: z.string().nullable().optional(),
  experiment_status: z.string().nullable().optional(),
  min_volume: z.number().nullable().optional(),
  volume_min_value: z.number().nullable().optional(),
  volume_unit: z.string().nullable().optional(),
});

export const experimentsSchema = z.array(experimentSchema);

export const recordSchema = z.object({
  id: z.number(),
  experiment_id: z.number(),
  session_id: z.string(),
  iteration_number: z.number().nullable().optional(),
  clicks: z.number().nullable().optional(),
  views: z.number().nullable().optional(),
  views_profile: z.number().nullable().optional(),
  inicia_test: z.number().nullable().optional(),
  organic_piece_type: z.string().nullable().optional(),
  likes: z.number().nullable().optional(),
  comments: z.number().nullable().optional(),
  shares: z.number().nullable().optional(),
  saves: z.number().nullable().optional(),
  video_url: z.string().nullable().optional(),
  views_finish_pct: z.number().nullable().optional(),
  retention_pct: z.number().nullable().optional(),
  avg_watch_time: z.number().nullable().optional(),
  video_duration: z.number().nullable().optional(),
  ctr: z.number().nullable().optional(),
  cpc: z.number().nullable().optional(),
  initiate_checkouts: z.number().nullable().optional(),
  view_content: z.number().nullable().optional(),
  lead_form: z.number().nullable().optional(),
  purchase: z.number().nullable().optional(),
  paid_video_duration: z.number().nullable().optional(),
  campaign_id: z.string().nullable().optional(),
  ad_set_id: z.string().nullable().optional(),
  ad_id: z.string().nullable().optional(),
  live_viewers_peak: z.number().nullable().optional(),
  live_avg_viewers: z.number().nullable().optional(),
  live_duration: z.number().nullable().optional(),
  live_new_followers: z.number().nullable().optional(),
  execution_type: z.string().nullable().optional(),
  record_name: z.string().nullable().optional(),
  public_id: z.number().nullable().optional(),
  publico: z.string().nullable().optional(),
  hook_text: z.string().nullable().optional(),
  hook_type: z.string().nullable().optional(),
  cta_text: z.string().nullable().optional(),
  cta_type: z.string().nullable().optional(),
  creative_id: z.string().nullable().optional(),
  record_status: z.string().nullable().optional(),
  drive_folder_path: z.string().nullable().optional(),
  created_at: z.string().nullable().optional(),
  updated_at: z.string().nullable().optional(),
});

export const recordsSchema = z.array(recordSchema);

export const publicSchema = z.object({
  id: z.number(),
  name: z.string(),
  description: z.string().nullable().optional(),
});

export const publicsSchema = z.array(publicSchema);

export const documentationSchema = z.object({
  notes: z
    .array(
      z.object({
        id: z.number(),
        body: z.string(),
        created_at: z.string(),
        updated_at: z.string().nullable().optional(),
      }),
    )
    .optional(),
});

export const aiAnalysisSchema = z.object({
  output: z.string(),
});

export const aiHistorySchema = z.array(
  z.object({
    id: z.number(),
    analysis_type: z.string(),
    output: z.string(),
    created_at: z.string(),
  }),
);
