-- Safe upgrade for an existing InterviewIQ database.
-- Back up the database before running this file.

ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS email_verified boolean DEFAULT false NOT NULL,
    ADD COLUMN IF NOT EXISTS email_verification_token_hash character varying(64),
    ADD COLUMN IF NOT EXISTS email_verification_expires_at timestamp without time zone,
    ADD COLUMN IF NOT EXISTS password_reset_token_hash character varying(64),
    ADD COLUMN IF NOT EXISTS password_reset_expires_at timestamp without time zone,
    ADD COLUMN IF NOT EXISTS password_changed_at timestamp without time zone;

CREATE TABLE IF NOT EXISTS public.interview_sessions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    resume_id uuid NOT NULL,
    resume_version integer NOT NULL,
    jd_id uuid NOT NULL,
    jd_version integer NOT NULL,
    interview_type character varying(20) DEFAULT 'mixed' NOT NULL,
    duration_seconds integer NOT NULL,
    status character varying(20) DEFAULT 'preparing' NOT NULL,
    current_turn_no integer DEFAULT 0 NOT NULL,
    questions_asked integer DEFAULT 0 NOT NULL,
    overall_score integer,
    started_at timestamp without time zone,
    ended_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT interview_sessions_duration_check
        CHECK (duration_seconds BETWEEN 60 AND 3600),
    CONSTRAINT interview_sessions_questions_check
        CHECK (questions_asked >= 0),
    CONSTRAINT interview_sessions_status_check
        CHECK (status IN ('preparing', 'active', 'completed', 'interrupted', 'failed')),
    CONSTRAINT interview_sessions_turn_check
        CHECK (current_turn_no >= 0),
    CONSTRAINT interview_sessions_type_check
        CHECK (interview_type IN ('technical', 'behavioral', 'mixed', 'resume_based')),
    CONSTRAINT interview_sessions_pkey PRIMARY KEY (id),
    CONSTRAINT interview_sessions_jd_id_fkey
        FOREIGN KEY (jd_id) REFERENCES public.job_descriptions(id),
    CONSTRAINT interview_sessions_resume_id_fkey
        FOREIGN KEY (resume_id) REFERENCES public.resumes(id),
    CONSTRAINT interview_sessions_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES public.users(id)
);

CREATE TABLE IF NOT EXISTS public.interview_turns (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    session_id uuid NOT NULL,
    turn_no integer NOT NULL,
    question_text text NOT NULL,
    question_category character varying(20) NOT NULL,
    difficulty character varying(10) NOT NULL,
    user_transcript text,
    answer_started_at timestamp without time zone,
    answer_ended_at timestamp without time zone,
    answer_duration_ms integer,
    answer_score integer,
    answer_feedback text,
    is_completed boolean DEFAULT false NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT interview_turn_category_check
        CHECK (question_category IN ('technical', 'behavioral', 'situational', 'resume_based', 'hr')),
    CONSTRAINT interview_turn_difficulty_check
        CHECK (difficulty IN ('easy', 'medium', 'hard')),
    CONSTRAINT interview_turns_pkey PRIMARY KEY (id),
    CONSTRAINT unique_interview_turn UNIQUE (session_id, turn_no),
    CONSTRAINT interview_turns_session_id_fkey
        FOREIGN KEY (session_id) REFERENCES public.interview_sessions(id)
);

CREATE TABLE IF NOT EXISTS public.interview_summaries (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    session_id uuid NOT NULL,
    user_id uuid NOT NULL,
    overall_score integer,
    strong_areas jsonb,
    weak_areas jsonb,
    skills_to_learn jsonb,
    job_requirements_missing jsonb,
    technical_feedback jsonb,
    behavioral_feedback jsonb,
    communication_feedback jsonb,
    recommendations jsonb,
    summary_text text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT interview_summaries_pkey PRIMARY KEY (id),
    CONSTRAINT interview_summaries_session_id_key UNIQUE (session_id),
    CONSTRAINT interview_summaries_session_id_fkey
        FOREIGN KEY (session_id) REFERENCES public.interview_sessions(id),
    CONSTRAINT interview_summaries_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES public.users(id)
);

CREATE TABLE IF NOT EXISTS public.voice_analyses (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    session_id uuid NOT NULL,
    turn_id uuid NOT NULL,
    transcript text,
    language character varying(16),
    speaking_rate_wpm integer,
    pause_count integer,
    long_pause_count integer,
    filler_word_count integer,
    repeated_word_count integer,
    grammar_score integer,
    fluency_score integer,
    clarity_score integer,
    pronunciation_score integer,
    confidence_score integer,
    pace_score integer,
    grammar_issues jsonb,
    filler_words jsonb,
    pronunciation_notes jsonb,
    voice_feedback text,
    analysis_status character varying(20) DEFAULT 'completed'::character varying NOT NULL,
    analysis_provider character varying(40),
    analysis_error text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT voice_analyses_pkey PRIMARY KEY (id),
    CONSTRAINT voice_analyses_turn_id_key UNIQUE (turn_id),
    CONSTRAINT voice_analyses_session_id_fkey
        FOREIGN KEY (session_id) REFERENCES public.interview_sessions(id),
    CONSTRAINT voice_analyses_turn_id_fkey
        FOREIGN KEY (turn_id) REFERENCES public.interview_turns(id)
);

ALTER TABLE public.voice_analyses
    ADD COLUMN IF NOT EXISTS analysis_status character varying(20)
        DEFAULT 'completed'::character varying NOT NULL;
ALTER TABLE public.voice_analyses
    ADD COLUMN IF NOT EXISTS analysis_provider character varying(40);
ALTER TABLE public.voice_analyses
    ADD COLUMN IF NOT EXISTS analysis_error text;

CREATE TABLE IF NOT EXISTS public.assistant_messages (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL REFERENCES public.users(id),
    role character varying(16) NOT NULL
        CHECK (role IN ('user', 'assistant')),
    content text NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT assistant_messages_pkey PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS idx_interview_sessions_user_created
    ON public.interview_sessions (user_id, created_at);

CREATE INDEX IF NOT EXISTS idx_interview_sessions_user_status
    ON public.interview_sessions (user_id, status);

CREATE INDEX IF NOT EXISTS idx_interview_turns_session_turn
    ON public.interview_turns (session_id, turn_no);

CREATE INDEX IF NOT EXISTS idx_interview_summaries_user_created
    ON public.interview_summaries (user_id, created_at);

CREATE INDEX IF NOT EXISTS idx_voice_analyses_session_created
    ON public.voice_analyses (session_id, created_at);

CREATE INDEX IF NOT EXISTS idx_assistant_messages_user_created
    ON public.assistant_messages (user_id, created_at);

CREATE UNIQUE INDEX IF NOT EXISTS uq_active_interview_per_user
    ON public.interview_sessions (user_id)
    WHERE status IN ('preparing', 'active');
