--
-- PostgreSQL database dump
--

\restrict lOQcpTCb7qOsmu0F2fFqsn0D2NIC0AA9bgDQQ3yb2otFog0i6Sp0wiZ6vNevlek

-- Dumped from database version 18.6 (Ubuntu 18.6-0ubuntu0.26.04.1)
-- Dumped by pg_dump version 18.6 (Ubuntu 18.6-0ubuntu0.26.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: job_descriptions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.job_descriptions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    version_no integer NOT NULL,
    job_description text NOT NULL,
    jd_hash character varying(64),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.job_descriptions OWNER TO postgres;

--
-- Name: questions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.questions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    batch_no integer NOT NULL,
    item_no integer NOT NULL,
    resume_id uuid NOT NULL,
    jd_id uuid NOT NULL,
    resume_version integer NOT NULL,
    jd_version integer NOT NULL,
    analysis_id uuid,
    category character varying(20) NOT NULL,
    difficulty character varying(10) NOT NULL,
    target_skill character varying(100),
    question_text text NOT NULL,
    question_hash character varying(64) NOT NULL,
    ideal_answer_points jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT questions_category_check CHECK (((category)::text = ANY ((ARRAY['technical'::character varying, 'behavioral'::character varying, 'situational'::character varying, 'resume_based'::character varying, 'hr'::character varying])::text[]))),
    CONSTRAINT questions_difficulty_check CHECK (((difficulty)::text = ANY ((ARRAY['easy'::character varying, 'medium'::character varying, 'hard'::character varying])::text[]))),
    CONSTRAINT unique_user_question_batch_item UNIQUE (user_id, batch_no, item_no)
);


ALTER TABLE public.questions OWNER TO postgres;

--
-- Name: resume_analysis; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.resume_analysis (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    analysis_version integer NOT NULL,
    resume_id uuid NOT NULL,
    jd_id uuid NOT NULL,
    resume_version integer NOT NULL,
    jd_version integer NOT NULL,
    overview text,
    match_analysis text,
    irrelevant_content text,
    missing_requirements text,
    suggestions text,
    others jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    analysis_hash character varying(64) NOT NULL
);


ALTER TABLE public.resume_analysis OWNER TO postgres;

--
-- Name: resumes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.resumes (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    version_no integer NOT NULL,
    file_name character varying(255),
    resume_text text NOT NULL,
    resume_hash character varying(64),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.resumes OWNER TO postgres;

--
-- Name: user_profile; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_profile (
    user_id uuid NOT NULL,
    current_resume_id uuid,
    current_resume_version integer,
    current_jd_id uuid,
    current_jd_version integer,
    current_analysis_id uuid,
    current_analysis_version integer,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.user_profile OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    email character varying(255) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    password_hash character varying(255) NOT NULL,
    email_verified boolean DEFAULT false NOT NULL,
    email_verification_token_hash character varying(64),
    email_verification_expires_at timestamp without time zone,
    password_reset_token_hash character varying(64),
    password_reset_expires_at timestamp without time zone,
    password_changed_at timestamp without time zone
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: interview_sessions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.interview_sessions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    resume_id uuid NOT NULL,
    resume_version integer NOT NULL,
    jd_id uuid NOT NULL,
    jd_version integer NOT NULL,
    interview_type character varying(20) DEFAULT 'mixed'::character varying NOT NULL,
    duration_seconds integer NOT NULL,
    status character varying(20) DEFAULT 'preparing'::character varying NOT NULL,
    current_turn_no integer DEFAULT 0 NOT NULL,
    questions_asked integer DEFAULT 0 NOT NULL,
    overall_score integer,
    started_at timestamp without time zone,
    ended_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT interview_sessions_duration_check CHECK ((duration_seconds BETWEEN 60 AND 3600)),
    CONSTRAINT interview_sessions_questions_check CHECK ((questions_asked >= 0)),
    CONSTRAINT interview_sessions_status_check CHECK (((status)::text = ANY ((ARRAY['preparing'::character varying, 'active'::character varying, 'completed'::character varying, 'interrupted'::character varying, 'failed'::character varying])::text[]))),
    CONSTRAINT interview_sessions_turn_check CHECK ((current_turn_no >= 0)),
    CONSTRAINT interview_sessions_type_check CHECK (((interview_type)::text = ANY ((ARRAY['technical'::character varying, 'behavioral'::character varying, 'mixed'::character varying, 'resume_based'::character varying])::text[])))
);

ALTER TABLE public.interview_sessions OWNER TO postgres;

--
-- Name: interview_turns; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.interview_turns (
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
    CONSTRAINT interview_turn_category_check CHECK (((question_category)::text = ANY ((ARRAY['technical'::character varying, 'behavioral'::character varying, 'situational'::character varying, 'resume_based'::character varying, 'hr'::character varying])::text[]))),
    CONSTRAINT interview_turn_difficulty_check CHECK (((difficulty)::text = ANY ((ARRAY['easy'::character varying, 'medium'::character varying, 'hard'::character varying])::text[]))),
    CONSTRAINT unique_interview_turn UNIQUE (session_id, turn_no)
);

ALTER TABLE public.interview_turns OWNER TO postgres;

--
-- Name: interview_summaries; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.interview_summaries (
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
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);

ALTER TABLE public.interview_summaries OWNER TO postgres;

--
-- Name: voice_analyses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.voice_analyses (
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
    UNIQUE (turn_id)
);

ALTER TABLE public.voice_analyses OWNER TO postgres;

--
-- Name: assistant_messages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.assistant_messages (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    role character varying(16) NOT NULL,
    content text NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT assistant_messages_role_check CHECK ((role)::text = ANY ((ARRAY['user'::character varying, 'assistant'::character varying])::text[]))
);

ALTER TABLE public.assistant_messages OWNER TO postgres;

--
-- Name: job_descriptions job_descriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.job_descriptions
    ADD CONSTRAINT job_descriptions_pkey PRIMARY KEY (id);


--
-- Name: questions questions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_pkey PRIMARY KEY (id);


--
-- Name: resume_analysis resume_analysis_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resume_analysis
    ADD CONSTRAINT resume_analysis_pkey PRIMARY KEY (id);


--
-- Name: resumes resumes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resumes
    ADD CONSTRAINT resumes_pkey PRIMARY KEY (id);


--
-- Name: resume_analysis unique_analysis_version; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resume_analysis
    ADD CONSTRAINT unique_analysis_version UNIQUE (user_id, analysis_version);


--
-- Name: job_descriptions unique_jd_version; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.job_descriptions
    ADD CONSTRAINT unique_jd_version UNIQUE (user_id, version_no);


--
-- Name: resumes unique_resume_version; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resumes
    ADD CONSTRAINT unique_resume_version UNIQUE (user_id, version_no);


--
-- Name: resume_analysis unique_user_analysis_hash; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resume_analysis
    ADD CONSTRAINT unique_user_analysis_hash UNIQUE (user_id, analysis_hash);


--
-- Name: questions unique_user_question_hash; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT unique_user_question_hash UNIQUE (user_id, question_hash);


--
-- Name: user_profile user_profile_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_profile
    ADD CONSTRAINT user_profile_pkey PRIMARY KEY (user_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_analysis_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_analysis_user ON public.resume_analysis USING btree (user_id);


--
-- Name: idx_analysis_user_version; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_analysis_user_version ON public.resume_analysis USING btree (user_id, analysis_version DESC);


--
-- Name: idx_jd_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_jd_user ON public.job_descriptions USING btree (user_id);


--
-- Name: idx_jd_user_version; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_jd_user_version ON public.job_descriptions USING btree (user_id, version_no DESC);


--
-- Name: idx_questions_user_batch; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_questions_user_batch ON public.questions USING btree (user_id, batch_no, item_no);


--
-- Name: idx_resume_user_version; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_resume_user_version ON public.resumes USING btree (user_id, version_no DESC);


--
-- Name: idx_resumes_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_resumes_user ON public.resumes USING btree (user_id);


--
-- Name: user_profile fk_current_analysis; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_profile
    ADD CONSTRAINT fk_current_analysis FOREIGN KEY (current_analysis_id) REFERENCES public.resume_analysis(id);


--
-- Name: user_profile fk_current_jd; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_profile
    ADD CONSTRAINT fk_current_jd FOREIGN KEY (current_jd_id) REFERENCES public.job_descriptions(id);


--
-- Name: user_profile fk_current_resume; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_profile
    ADD CONSTRAINT fk_current_resume FOREIGN KEY (current_resume_id) REFERENCES public.resumes(id);


--
-- Name: job_descriptions job_descriptions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.job_descriptions
    ADD CONSTRAINT job_descriptions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: questions questions_analysis_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_analysis_id_fkey FOREIGN KEY (analysis_id) REFERENCES public.resume_analysis(id);


--
-- Name: questions questions_jd_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_jd_id_fkey FOREIGN KEY (jd_id) REFERENCES public.job_descriptions(id);


--
-- Name: questions questions_resume_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_resume_id_fkey FOREIGN KEY (resume_id) REFERENCES public.resumes(id);


--
-- Name: questions questions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: resume_analysis resume_analysis_jd_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resume_analysis
    ADD CONSTRAINT resume_analysis_jd_id_fkey FOREIGN KEY (jd_id) REFERENCES public.job_descriptions(id);


--
-- Name: resume_analysis resume_analysis_resume_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resume_analysis
    ADD CONSTRAINT resume_analysis_resume_id_fkey FOREIGN KEY (resume_id) REFERENCES public.resumes(id);


--
-- Name: resume_analysis resume_analysis_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resume_analysis
    ADD CONSTRAINT resume_analysis_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: resumes resumes_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resumes
    ADD CONSTRAINT resumes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: user_profile user_profile_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_profile
    ADD CONSTRAINT user_profile_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);

--
-- Name: interview_sessions interview_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.interview_sessions
    ADD CONSTRAINT interview_sessions_pkey PRIMARY KEY (id);

--
-- Name: interview_turns interview_turns_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.interview_turns
    ADD CONSTRAINT interview_turns_pkey PRIMARY KEY (id);

--
-- Name: interview_summaries interview_summaries_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.interview_summaries
    ADD CONSTRAINT interview_summaries_pkey PRIMARY KEY (id);

--
-- Name: interview_summaries interview_summaries_session_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.interview_summaries
    ADD CONSTRAINT interview_summaries_session_id_key UNIQUE (session_id);

--
-- Name: voice_analyses voice_analyses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.voice_analyses
    ADD CONSTRAINT voice_analyses_pkey PRIMARY KEY (id);

--
-- Name: assistant_messages assistant_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.assistant_messages
    ADD CONSTRAINT assistant_messages_pkey PRIMARY KEY (id);

--
-- Name: interview_sessions user active session; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX uq_active_interview_per_user
    ON public.interview_sessions USING btree (user_id)
    WHERE ((status)::text = ANY ((ARRAY['preparing'::character varying, 'active'::character varying])::text[]));

--
-- Name: idx_interview_sessions_user_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_interview_sessions_user_created
    ON public.interview_sessions USING btree (user_id, created_at);

--
-- Name: idx_interview_sessions_user_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_interview_sessions_user_status
    ON public.interview_sessions USING btree (user_id, status);

--
-- Name: idx_interview_turns_session_turn; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_interview_turns_session_turn
    ON public.interview_turns USING btree (session_id, turn_no);

--
-- Name: idx_interview_summaries_user_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_interview_summaries_user_created
    ON public.interview_summaries USING btree (user_id, created_at);

--
-- Name: idx_voice_analyses_session_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_voice_analyses_session_created
    ON public.voice_analyses USING btree (session_id, created_at);

--
-- Name: idx_assistant_messages_user_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_assistant_messages_user_created
    ON public.assistant_messages USING btree (user_id, created_at);

--
-- Name: interview_sessions interview_sessions_jd_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.interview_sessions
    ADD CONSTRAINT interview_sessions_jd_id_fkey FOREIGN KEY (jd_id) REFERENCES public.job_descriptions(id);

--
-- Name: interview_sessions interview_sessions_resume_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.interview_sessions
    ADD CONSTRAINT interview_sessions_resume_id_fkey FOREIGN KEY (resume_id) REFERENCES public.resumes(id);

--
-- Name: interview_sessions interview_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.interview_sessions
    ADD CONSTRAINT interview_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);

--
-- Name: interview_turns interview_turns_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.interview_turns
    ADD CONSTRAINT interview_turns_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.interview_sessions(id);

--
-- Name: interview_summaries interview_summaries_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.interview_summaries
    ADD CONSTRAINT interview_summaries_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.interview_sessions(id);

--
-- Name: interview_summaries interview_summaries_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.interview_summaries
    ADD CONSTRAINT interview_summaries_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);

--
-- Name: voice_analyses voice_analyses_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.voice_analyses
    ADD CONSTRAINT voice_analyses_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.interview_sessions(id);

--
-- Name: voice_analyses voice_analyses_turn_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.voice_analyses
    ADD CONSTRAINT voice_analyses_turn_id_fkey FOREIGN KEY (turn_id) REFERENCES public.interview_turns(id);

--
-- Name: assistant_messages assistant_messages_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.assistant_messages
    ADD CONSTRAINT assistant_messages_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);

--
-- PostgreSQL database dump complete
--

\unrestrict lOQcpTCb7qOsmu0F2fFqsn0D2NIC0AA9bgDQQ3yb2otFog0i6Sp0wiZ6vNevlek

