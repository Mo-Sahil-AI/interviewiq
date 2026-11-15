--
-- PostgreSQL database dump
--

\restrict v6xtLMu5YW9FTEbYpxnSEk9nKTfCWzjTiwbrw7JiAaoRadPgKhEf2rVdJILyDXV

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
    CONSTRAINT questions_difficulty_check CHECK (((difficulty)::text = ANY ((ARRAY['easy'::character varying, 'medium'::character varying, 'hard'::character varying])::text[])))
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
    password_hash character varying(255) NOT NULL
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Data for Name: job_descriptions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.job_descriptions (id, user_id, version_no, job_description, jd_hash, created_at) FROM stdin;
f3fb64a8-4c3e-4379-a073-c0d22444fc27	33ffc80d-c49f-4232-81be-dfbeb630cbe7	1	ML_Engineer	48330d873685bd8c8a53f4e655f1b333674298178dfd850774f1a7df9c8da7cc	2026-10-30 10:52:38.890349
ea53e4c9-b030-4248-89bd-98a25a07ed0b	33ffc80d-c49f-4232-81be-dfbeb630cbe7	2	AI_Engineer	4c6de4ca846036de6096ffa9927404bb9ba6312db8114227970b7ab6793d6375	2026-10-30 10:53:40.086036
bd9ee2a7-e10a-488c-a861-6b71d8bb83b3	33ffc80d-c49f-4232-81be-dfbeb630cbe7	3	My passion is to become ML and AI engineer	1499b3af79b57a73fd6ef93e307b2a1b002864d3ae9bd6be998c93dad28e9f52	2026-10-30 10:57:20.470422
3bb6c927-69ab-4bbf-85c6-a163d7193d03	897955fe-f0e4-44c3-a4c9-04340cc8e9e7	1	AI_Engineer	4c6de4ca846036de6096ffa9927404bb9ba6312db8114227970b7ab6793d6375	2026-10-30 11:28:20.373788
6012089c-d183-4ccc-9dd7-c23b03bb08eb	d15bda3f-2d1b-48b3-8838-078c2593879b	1	AI and ML Engineer	f60f01aa85e98fb1f7c6060718d13d64d0f67ac131cc2389e1cbe5ca8b2d3e8f	2026-11-07 21:52:51.090529
\.


--
-- Data for Name: questions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.questions (id, user_id, batch_no, item_no, resume_id, jd_id, resume_version, jd_version, analysis_id, category, difficulty, target_skill, question_text, question_hash, ideal_answer_points, created_at) FROM stdin;
2029507c-d44d-490e-a016-9f8387ea270a	33ffc80d-c49f-4232-81be-dfbeb630cbe7	1	1	7dbefdba-82b1-419b-8686-bd42d410d658	bd9ee2a7-e10a-488c-a861-6b71d8bb83b3	2	3	74f3dd05-b046-49a3-a088-5009890d71f1	technical	easy	Python Programming	What is the difference between a list and a tuple in Python?	24c01d1fc4b2825b942589c44e292b1c9fe6b6b52d2bd4b6a6bce58822595baf	["Lists are mutable while tuples are immutable", "Lists use square brackets [] while tuples use parentheses ()", "Tuples are generally more memory efficient and hashable"]	2026-11-11 05:53:32.128678
07f0a287-65ab-4c06-8879-53cba13f5b20	33ffc80d-c49f-4232-81be-dfbeb630cbe7	1	2	7dbefdba-82b1-419b-8686-bd42d410d658	bd9ee2a7-e10a-488c-a861-6b71d8bb83b3	2	3	74f3dd05-b046-49a3-a088-5009890d71f1	technical	easy	Machine Learning	What is the main difference between supervised and unsupervised learning?	c749b6a6107478ae87ad156e1d3ac3d95616b35cf6697f692d7ece8f5776c036	["Supervised learning uses labeled data for training", "Unsupervised learning finds hidden patterns in unlabeled data", "Examples include classification for supervised and clustering for unsupervised"]	2026-11-11 05:53:32.128678
f8728ecb-87b1-4948-aca3-1d95325f4ee1	33ffc80d-c49f-4232-81be-dfbeb630cbe7	1	3	7dbefdba-82b1-419b-8686-bd42d410d658	bd9ee2a7-e10a-488c-a861-6b71d8bb83b3	2	3	74f3dd05-b046-49a3-a088-5009890d71f1	technical	easy	Data Structures	How does a hash table store and retrieve data efficiently?	06856a6ed7c8af662d54acc8ec789231e204c36ce8b66678e480eb5e5d6727dd	["Uses a hash function to compute an index for keys", "Maps keys to specific memory locations for fast access", "Provides average O(1) time complexity for lookups"]	2026-11-11 05:53:32.128678
640ef0bb-fabf-4562-b9f6-62044f1acc7f	33ffc80d-c49f-4232-81be-dfbeb630cbe7	1	4	7dbefdba-82b1-419b-8686-bd42d410d658	bd9ee2a7-e10a-488c-a861-6b71d8bb83b3	2	3	74f3dd05-b046-49a3-a088-5009890d71f1	technical	easy	Scikit-learn	How do you handle missing values in a dataset before training a model using scikit-learn?	cfa30ec40ea6c21212f81c534b0f450542a9ff05799320170ed096e1af45280f	["Using the SimpleImputer class", "Replacing missing values with mean, median, or mode", "Dropping rows or columns with missing data if appropriate"]	2026-11-11 05:53:32.128678
01c87f36-d612-4396-a191-f27e700102ab	33ffc80d-c49f-4232-81be-dfbeb630cbe7	1	5	7dbefdba-82b1-419b-8686-bd42d410d658	bd9ee2a7-e10a-488c-a861-6b71d8bb83b3	2	3	74f3dd05-b046-49a3-a088-5009890d71f1	technical	easy	TensorFlow	What is the role of an activation function in a neural network layer built with TensorFlow?	1bd30167f8a2eb3e0189a035c6e7cdd66f456c6c07f49e74a29cfc74fc41bb6c	["Introduces non-linearity into the network", "Allows the model to learn complex patterns", "Common examples include ReLU, sigmoid, and tanh"]	2026-11-11 05:53:32.128678
ddecb98d-b861-4fc4-b499-f22364428974	33ffc80d-c49f-4232-81be-dfbeb630cbe7	1	6	7dbefdba-82b1-419b-8686-bd42d410d658	bd9ee2a7-e10a-488c-a861-6b71d8bb83b3	2	3	74f3dd05-b046-49a3-a088-5009890d71f1	technical	easy	Git	What is the purpose of the git commit command?	0c12046b802836c8860a3df13249a8127c09bfab98400dfb140e00b4ff3cc5dd	["Saves changes to the local repository", "Creates a snapshot of the staged changes", "Requires a descriptive message explaining the update"]	2026-11-11 05:53:32.128678
1fbde9ad-fd4e-4667-b57b-470555fdc140	33ffc80d-c49f-4232-81be-dfbeb630cbe7	1	7	7dbefdba-82b1-419b-8686-bd42d410d658	bd9ee2a7-e10a-488c-a861-6b71d8bb83b3	2	3	74f3dd05-b046-49a3-a088-5009890d71f1	technical	easy	Google Cloud Platform	What is Google Cloud Storage used for in cloud computing?	528a01073bf1e8fc6667d0d953feeaa5669ef4da7dee1721f78718d67bc90ace	["Object storage for unstructured data", "Storing files, images, and backups securely", "Accessible via HTTP/HTTPS globally"]	2026-11-11 05:53:32.128678
4b2993fa-75a5-4ad8-8d87-2a73563c7c29	33ffc80d-c49f-4232-81be-dfbeb630cbe7	1	8	7dbefdba-82b1-419b-8686-bd42d410d658	bd9ee2a7-e10a-488c-a861-6b71d8bb83b3	2	3	74f3dd05-b046-49a3-a088-5009890d71f1	technical	easy	C++	What is a pointer in C++ and how does it store data?	78bff805d0b557f481ce56ffddc76a4342216cd21bca727113f3eae4067df1f4	["A variable that stores the memory address of another variable", "Declared using the asterisk symbol (*)", "Allows dynamic memory management and efficient array handling"]	2026-11-11 05:53:32.128678
e01d5955-dfab-4717-b885-20e903f2557e	33ffc80d-c49f-4232-81be-dfbeb630cbe7	1	9	7dbefdba-82b1-419b-8686-bd42d410d658	bd9ee2a7-e10a-488c-a861-6b71d8bb83b3	2	3	74f3dd05-b046-49a3-a088-5009890d71f1	technical	easy	Computer Vision	How is a digital color image typically represented in computer vision?	dda096a6cacfa31b0ab81522ef81d302363325fe758afee17c2979c1ff609e18	["As a 3D NumPy array of height, width, and color channels", "Using RGB values ranging from 0 to 255 per channel", "Pixels represent individual intensity or color points"]	2026-11-11 05:53:32.128678
cc2b2dd2-7fb1-4f17-bb65-19b7c1be34c3	33ffc80d-c49f-4232-81be-dfbeb630cbe7	1	10	7dbefdba-82b1-419b-8686-bd42d410d658	bd9ee2a7-e10a-488c-a861-6b71d8bb83b3	2	3	74f3dd05-b046-49a3-a088-5009890d71f1	technical	easy	Statistical Analysis	What does the standard deviation measure in a dataset?	246c78c9d7faf4104fb58526a341cf552718f065e4fca0568b66bf1d80e32fff	["The amount of variation or dispersion of a set of values", "The square root of the variance", "How far data points typically spread from the mean"]	2026-11-11 05:53:32.128678
291ab45f-51c8-43f3-b7f6-19e8600f75d5	33ffc80d-c49f-4232-81be-dfbeb630cbe7	2	1	7dbefdba-82b1-419b-8686-bd42d410d658	bd9ee2a7-e10a-488c-a861-6b71d8bb83b3	2	3	74f3dd05-b046-49a3-a088-5009890d71f1	technical	medium	Surrogate Modeling	How do you evaluate the accuracy versus speed trade-off when replacing a heavy simulation like DWSIM with a machine learning surrogate model?	abb0fcde811e420af191b5db44d7200e9c7d5fc5764b9dff20dde59e60492bd3	["Measuring inference time reduction against the full simulation run time", "Using validation metrics such as Mean Squared Error or R-squared on unseen simulation parameters", "Ensuring physical plausibility and boundary constraints are respected by the surrogate outputs"]	2026-11-11 06:26:04.218275
6201b0b9-174f-47df-8e65-9a3c9154aa2c	33ffc80d-c49f-4232-81be-dfbeb630cbe7	2	2	7dbefdba-82b1-419b-8686-bd42d410d658	bd9ee2a7-e10a-488c-a861-6b71d8bb83b3	2	3	74f3dd05-b046-49a3-a088-5009890d71f1	technical	hard	Medical Imaging	What specific preprocessing steps are crucial for volumetric medical imaging datasets like DaT scans before feeding them into a convolutional neural network?	65eedf630a340505358d6036b36db6346a6c7c5322563b6a801172e90de2a957	["Intensity normalization and voxel resampling to a standard resolution", "Skull stripping or region of interest cropping to reduce background noise", "Data augmentation tailored to medical constraints such as slight rotations and scaling"]	2026-11-11 06:26:04.218275
dd5ea911-1bf4-4551-bb2f-868b42b34bb3	33ffc80d-c49f-4232-81be-dfbeb630cbe7	2	3	7dbefdba-82b1-419b-8686-bd42d410d658	bd9ee2a7-e10a-488c-a861-6b71d8bb83b3	2	3	74f3dd05-b046-49a3-a088-5009890d71f1	technical	medium	Transfer Learning	When adapting a general domain vision model for specialized medical imaging, what are the trade-offs between fine-tuning all layers versus freezing the feature extractor?	0db8bcdced2fade919537fbc708bc72ef26a0db621b6a3c67d25be20c8c59cc0	["Freezing prevents catastrophic forgetting and works well with smaller medical datasets", "Fine-tuning allows early layers to learn domain-specific edge and texture filters", "Risk of overfitting increases when fine-tuning deep networks on limited medical data"]	2026-11-11 06:26:04.218275
a14b8216-f922-4f4a-93af-31298f11e078	33ffc80d-c49f-4232-81be-dfbeb630cbe7	2	4	7dbefdba-82b1-419b-8686-bd42d410d658	bd9ee2a7-e10a-488c-a861-6b71d8bb83b3	2	3	74f3dd05-b046-49a3-a088-5009890d71f1	technical	easy	PyTorch	What is the role of torch.no_grad() when evaluating or validating a PyTorch deep learning model?	23b870a1807e867c65063db2231e864a6a296d80f8ffa71a3e4ee3cbb0c064f6	["Disables gradient calculation to reduce memory consumption", "Speeds up computation during the inference or evaluation phase", "Prevents accidental weight updates during validation loops"]	2026-11-11 06:26:04.218275
39f4fba7-c12b-429b-b186-1f7fe0a43c55	33ffc80d-c49f-4232-81be-dfbeb630cbe7	2	5	7dbefdba-82b1-419b-8686-bd42d410d658	bd9ee2a7-e10a-488c-a861-6b71d8bb83b3	2	3	74f3dd05-b046-49a3-a088-5009890d71f1	technical	medium	C++ Data Structures	How does a standard priority queue differ from a standard queue in C++, and under what algorithmic scenario would you use it in ML?	5db0960b5742cd99ebac5086097aab3f3b7e90cc23e302824d1cfda0f563abbd	["Priority queue retrieves elements based on priority rather than FIFO order", "Typically implemented using a binary heap under the hood in C++ STL", "Used in algorithms like Dijkstra's or finding the top-K nearest neighbors"]	2026-11-11 06:26:04.218275
f6670c7d-47f3-482c-8597-0cfe831c3d95	33ffc80d-c49f-4232-81be-dfbeb630cbe7	2	6	7dbefdba-82b1-419b-8686-bd42d410d658	bd9ee2a7-e10a-488c-a861-6b71d8bb83b3	2	3	74f3dd05-b046-49a3-a088-5009890d71f1	technical	hard	Model Architecture Design	How do skip connections in ResNet architectures mitigate the vanishing gradient problem in deep neural networks?	82b5ecc9b8a5bd40fc451e59078d29fe85a914bc4e491be9b9b4abd00aeb695a	["They create an alternate pathway for gradients to flow backward directly", "They allow layers to learn residual mappings rather than unreferenced functions", "They help maintain gradient magnitude across very deep network stacks"]	2026-11-11 06:26:04.218275
ad970f33-e3d8-4323-9a09-dfcfee1f36be	33ffc80d-c49f-4232-81be-dfbeb630cbe7	2	7	7dbefdba-82b1-419b-8686-bd42d410d658	bd9ee2a7-e10a-488c-a861-6b71d8bb83b3	2	3	74f3dd05-b046-49a3-a088-5009890d71f1	technical	medium	Google Cloud Platform	How would you deploy a trained TensorFlow or PyTorch model as a scalable prediction service using Google Cloud Platform tools?	66a99be212ba56740cd067f64877a9d47f1b8c5b74a9b3c771a44d68d1745e1b	["Utilizing Vertex AI for managed model training and endpoint deployment", "Containerizing the model application using Docker and deploying on Cloud Run", "Setting up Cloud Logging and Monitoring for tracking prediction latency and errors"]	2026-11-11 06:26:04.218275
7780168c-d163-4346-8c86-0b094b675286	33ffc80d-c49f-4232-81be-dfbeb630cbe7	2	8	7dbefdba-82b1-419b-8686-bd42d410d658	bd9ee2a7-e10a-488c-a861-6b71d8bb83b3	2	3	74f3dd05-b046-49a3-a088-5009890d71f1	technical	easy	Python Advanced	What are Python generators and how do they help optimize memory usage when processing large datasets?	88bbc54c487995ecf1f5ad9912f78fb8610869de145044b88dc300d7b11251aa	["Generators use the yield keyword to produce values on-the-fly instead of storing them in memory", "They maintain state between iterations, enabling lazy evaluation", "Particularly useful for streaming large CSV or image files batch by batch"]	2026-11-11 06:26:04.218275
6b36f143-2d8e-41d3-97fc-5d77611e3291	33ffc80d-c49f-4232-81be-dfbeb630cbe7	2	9	7dbefdba-82b1-419b-8686-bd42d410d658	bd9ee2a7-e10a-488c-a861-6b71d8bb83b3	2	3	74f3dd05-b046-49a3-a088-5009890d71f1	technical	hard	Algorithm Optimization	Explain how memoization can be applied to optimize recursive dynamic programming solutions, and discuss its space-time complexity trade-offs.	c435682b5bcd1ee255aa6b28a7b9c80b81a8b5ef37c1c71c2466624e5a98adbe	["Storing results of expensive function calls and returning the cached result when the same inputs occur", "Reduces exponential time complexity to polynomial or linear time", "Increases space complexity due to the storage required for the cache table or memo dictionary"]	2026-11-11 06:26:04.218275
ff7ae430-af79-49f4-a7ba-382672729eb6	33ffc80d-c49f-4232-81be-dfbeb630cbe7	2	10	7dbefdba-82b1-419b-8686-bd42d410d658	bd9ee2a7-e10a-488c-a861-6b71d8bb83b3	2	3	74f3dd05-b046-49a3-a088-5009890d71f1	technical	medium	Computer Vision	What is the difference between semantic segmentation and instance segmentation in computer vision applications?	b0f2edcf71b4ff8d7337d81da73ae576d259d4ee60975aaaf76d54ffa2560de2	["Semantic segmentation classifies every pixel into a category without distinguishing individual objects", "Instance segmentation detects and delineates each distinct object of the same class separately", "Instance segmentation requires bounding box detection combined with pixel-level masking"]	2026-11-11 06:26:04.218275
\.


--
-- Data for Name: resume_analysis; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.resume_analysis (id, user_id, analysis_version, resume_id, jd_id, resume_version, jd_version, overview, match_analysis, irrelevant_content, missing_requirements, suggestions, others, created_at, analysis_hash) FROM stdin;
a0302522-e45e-40b6-b9df-10351923763d	33ffc80d-c49f-4232-81be-dfbeb630cbe7	1	42ca185b-209c-4223-9976-1771dd0524e9	f3fb64a8-4c3e-4379-a073-c0d22444fc27	1	1	The resume belongs to Mo Sahil, an AI/ML Research Intern and B.Tech Computer Engineering student with a strong academic background and foundational projects in machine learning, Python, and surrogate modelling.	The candidate presents a solid academic foundation with a 9.151 CGPA and relevant exposure to Python, Scikit-learn, and machine learning concepts. However, the job description is extremely brief ('ML_Engineer'), making it difficult to perform a comprehensive alignment beyond core ML competencies.	Inclusion of high school (Class 12) details and basic productivity workshops (e.g., be10X) are less relevant for an advanced ML Engineer role.	Given the sparse job description, specific enterprise frameworks, cloud deployment platforms (AWS/GCP/Azure), MLOps tools, and production-level experience cannot be explicitly verified from the resume.	Provide a detailed job description containing specific technical stack requirements, years of experience, and responsibilities to enable a more targeted resume optimization.	{"strengths": ["Strong academic record with a 9.151 CGPA", "Demonstrated hands-on experience with Python and Machine Learning projects", "Involvement in active research initiatives like medical imaging foundation models"], "keywords_matched": ["Python", "Machine Learning", "Scikit-learn", "Artificial Intelligence", "Data Processing"]}	2026-10-30 10:52:38.944897	7e9eb31b90b9f3c9c3153cd2e4162ed9bd5b2cfdcd81029305e16557f131d16c
d2dd06b9-1538-4369-aa9d-d9d59a02c3e7	33ffc80d-c49f-4232-81be-dfbeb630cbe7	2	42ca185b-209c-4223-9976-1771dd0524e9	ea53e4c9-b030-4248-89bd-98a25a07ed0b	1	2	The resume belongs to Mo Sahil, an AI/ML Research Intern and B.Tech Computer Engineering student with a strong academic record (9.151 CGPA). The job description provided is extremely sparse, simply stating 'AI_Engineer'.	Due to the minimal job description ('AI_Engineer'), a precise match analysis is challenging. However, the candidate demonstrates relevant foundational skills in Python, Machine Learning, Scikit-learn, and ongoing work in deep learning frameworks like TensorFlow and PyTorch, which align with a general AI Engineer role.	None identified, as the resume is concise and focused on computer engineering, AI/ML research, projects, and relevant certifications.	Cannot be precisely determined due to the lack of specific requirements in the job description.	Provide a detailed job description containing specific technical requirements, years of experience, and expected frameworks to get a more accurate evaluation and gap analysis.	{"strengths": ["Strong academic background with a 9.151 CGPA in AI Engineering", "Demonstrated practical experience in machine learning projects and surrogate modeling", "Active engagement in research projects involving medical imaging and foundational models"], "keywords_matched": ["AI", "Machine Learning", "Python", "Data Processing"]}	2026-10-30 10:53:40.109025	715f9e72dd90102c0a9b5843aa88b4508d4306f6f580725370bd5ccab662e06c
a18b6ce2-a529-4e1f-967c-da917bc3cd3c	33ffc80d-c49f-4232-81be-dfbeb630cbe7	3	42ca185b-209c-4223-9976-1771dd0524e9	bd9ee2a7-e10a-488c-a861-6b71d8bb83b3	1	3	The resume belongs to an AI/ML Research Intern with a strong academic background in Computer Engineering and practical experience in Python, machine learning, and surrogate modeling. The provided job description is extremely brief and informal ('My passion is to become ML and AI engineer'), indicating an entry-level or foundational aspiration toward ML/AI engineering.	The candidate's education, projects, and stated passion align well with an entry-level goal of becoming an ML and AI engineer. The candidate possesses foundational skills in Python, Scikit-learn, machine learning, and ongoing work in foundational models and surrogate modeling.	The section detailing language proficiencies (Urdu, Hindi, English) is standard but minor for a technical role, though not strictly irrelevant.	Because the job description is only a single sentence expressing a career aspiration rather than a detailed technical specification, no specific missing requirements can be definitively identified.	Expand the job description with specific technical requirements, frameworks (like PyTorch or TensorFlow), and years of experience to allow for a more rigorous and detailed resume comparison.	{"strengths": ["Strong academic record with a 9.151 CGPA in B.Tech Computer Engineering (AI)", "Hands-on project experience in machine learning surrogate modeling and medical imaging foundational models", "Proficiency in Python and core data science libraries like Scikit-learn"], "keywords_matched": ["Machine Learning", "AI", "Python"]}	2026-10-30 10:57:20.492257	b67046aaebbce2d9c6e1e1ed4fdbdcd129d73b02e178e983bdad41905a807b36
fa531d55-692d-464b-adf0-d85f8a1ba6b3	897955fe-f0e4-44c3-a4c9-04340cc8e9e7	1	8ae5de1c-dfb3-41ed-ad11-490dc46ec0f9	3bb6c927-69ab-4bbf-85c6-a163d7193d03	1	1	The resume belongs to an AI/ML Research Intern with a strong academic background in Computer Engineering (AI), solid Python skills, and experience in machine learning projects such as surrogate modelling and medical imaging. The job description is extremely brief ('AI_Engineer'), indicating a general alignment with foundational AI/ML roles.	The candidate's education in AI engineering, hands-on projects involving machine learning, artificial neural networks, and Python proficiency closely align with the core competencies expected of an AI Engineer.	The inclusion of basic productivity tool workshops (like be10X) and tutoring experience are slightly peripheral to a rigorous engineering role, though mostly harmless.	Due to the minimal job description ('AI_Engineer'), specific framework requirements like production-level deployment, MLOps, cloud-native AI infrastructure, or extensive industry experience cannot be explicitly verified, though the candidate is currently learning TensorFlow, PyTorch, and cloud platforms.	Transition learning goals (TensorFlow, PyTorch, Computer Vision) into active, production-ready project implementations. Add quantifiable metrics to project outcomes where possible.	{"strengths": ["Strong academic record (9.151 CGPA)", "Active research involvement in medical imaging and surrogate modelling", "Proficiency in Python and core machine learning libraries like Scikit-learn"], "keywords_matched": ["Python", "Machine Learning", "Artificial Intelligence", "Data Processing", "Research"]}	2026-10-30 11:28:20.390801	06591b11fa161c8a6e7158e2e7a01fc95b7b70fdbcf78800d0f2e76e19374a5a
f08b2a1d-3010-4408-a9fe-fb966ef37830	897955fe-f0e4-44c3-a4c9-04340cc8e9e7	2	eafc2377-467a-4ce6-a0ad-2047caa88996	3bb6c927-69ab-4bbf-85c6-a163d7193d03	2	1	The resume belongs to Mo Sahil, a Computer Engineering (AI) undergraduate at AMU with a strong academic record (9.151 CGPA), hands-on project experience in machine learning, and certifications in Python and Google Cloud. The job description provided is extremely brief, simply stating 'AI_Engineer'.	The candidate's educational background in Computer Engineering with a specialization in Artificial Intelligence, combined with practical experience in Python, TensorFlow, Scikit-learn, and machine learning projects (such as DWSIM surrogate modeling and medical imaging), aligns very well with a general AI Engineer role.	None identified. All sections, including education, technical skills, projects, and certifications, are directly relevant to artificial intelligence and software engineering.	Due to the lack of specific requirements in the job description beyond the title 'AI_Engineer', no specific missing technical requirements can be definitively identified.	Provide a more detailed job description containing specific technology stacks, years of experience, and responsibilities to enable a more granular and precise resume gap analysis.	{"strengths": ["High academic performance with a 9.151 CGPA in AI Engineering", "Strong foundation in Python and C++ for data structures and algorithms", "Practical project experience in Machine Learning, Computer Vision, and Process Optimization", "Active engagement in continuous learning through Google Cloud and Harvard certifications"], "keywords_matched": ["Python", "TensorFlow", "Scikit-learn", "Machine Learning", "Computer Vision", "Artificial Intelligence", "Data Structures & Algorithms"]}	2026-10-30 11:29:32.316055	1ce8dcdddb2c6930b8b2a742596343c6c996548e46a254b567c89a54897d61e2
74f3dd05-b046-49a3-a088-5009890d71f1	33ffc80d-c49f-4232-81be-dfbeb630cbe7	4	7dbefdba-82b1-419b-8686-bd42d410d658	bd9ee2a7-e10a-488c-a861-6b71d8bb83b3	2	3	The candidate, Mo Sahil, is a Computer Engineering undergraduate specializing in Artificial Intelligence with a strong academic background, practical ML project experience, and solid Python skills. The provided job description is extremely brief and informal, simply stating a passion for becoming an ML and AI engineer.	The candidate's profile strongly aligns with the goal of becoming an ML/AI engineer, as evidenced by coursework, projects in machine learning and computer vision, and technical proficiencies in Python, TensorFlow, and Scikit-learn.	Details regarding high school achievements, specific board names, and certain extracurricular certifications could be considered secondary, though they demonstrate a strong academic track record.	No specific technical requirements or qualifications were stated in the job description to identify as missing.	The candidate should seek out job descriptions with detailed technical and professional requirements to better tailor their resume for specific roles.	{"strengths": ["High CGPA (9.151/10) in Computer Engineering (AI)", "Strong foundation in Python and machine learning frameworks", "Hands-on project experience in AI, ML, and computer vision", "Active involvement in cloud technologies and research"], "keywords_matched": ["Machine Learning", "Artificial Intelligence", "Python", "TensorFlow", "Computer Vision"]}	2026-11-07 21:51:10.409932	8602dc2f97a4016806ff98022af3e5d77fe6c6c9a6b10b92f4cc40b68184e1c1
88797ef1-5a06-4830-8cff-ca56bf476881	d15bda3f-2d1b-48b3-8838-078c2593879b	1	4ae5beb9-a84a-4f3c-865d-f1a511458498	6012089c-d183-4ccc-9dd7-c23b03bb08eb	1	1	The candidate, Mo Sahil, is a second-year B.Tech student in Computer Engineering (Artificial Intelligence) with a strong academic record (CGPA 9.151) and practical experience in Python, C++, machine learning, and computer vision projects.	The candidate's educational focus in AI, hands-on experience with machine learning frameworks, Python proficiency (Harvard CS50P), and ongoing medical imaging computer vision projects align very well with the requirements of an AI and ML Engineer role.	The document is structured as an academic recommendation letter rather than a standard resume, containing introductory and concluding remarks suited for an internship committee.	As the job description is extremely brief ('AI and ML Engineer'), no explicit missing requirements can be identified, though formal industry work experience is not detailed in the provided text.	The candidate should convert this recommendation letter and academic background into a formal, traditional resume format highlighting specific projects, quantifiable achievements, and deployed AI/ML models.	{"strengths": ["Strong academic performance with a 9.151 CGPA in Computer Engineering (AI)", "Practical experience in Python and C++", "Active involvement in machine learning and medical imaging computer vision projects", "Solid foundation in data structures, algorithms, and applied mathematics"], "keywords_matched": ["Artificial Intelligence", "Machine Learning", "Python", "C++", "Data Structures and Algorithms", "Computer Vision", "Google Cloud Platform"]}	2026-11-07 21:52:51.108293	c07c8b5ee88a90530a51f26eefd9fb8b8cf4a31e2a2061d8780d8d54b467e915
\.


--
-- Data for Name: resumes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.resumes (id, user_id, version_no, file_name, resume_text, resume_hash, created_at) FROM stdin;
42ca185b-209c-4223-9976-1771dd0524e9	33ffc80d-c49f-4232-81be-dfbeb630cbe7	1	MITACS_CV_Final_Mo_Sahil.pdf	MO SAHIL\nAI/ML Research Intern\nAligarh, Uttar Pradesh | +91-7355378953 | kas2029.mohammedsahil@gmail.com\nGitHub: github.com/Mo-Sahil-AI | LinkedIn: linkedin.com/in/mo-sahil-6903803a0 | Google Dev: g.dev/mosahil\nEDUCATION\nB.Tech Computer Engineering (Artificial Intelligence)\nZakir Husain College of Engineering and Technology, AMU | July 2025 - Present\nCGPA: 9.151/10 • A+ Grades: Applied Mathematics I & II, Python Programming Lab, Applied Chemistry, Principles of\nElectronics Engineering\nSenior Secondary (Class 12)\nSaiyyid Hamid Senior Secondary School, Aligarh | 2025\nScore: 94.4% • Computer Science: 97 • Mathematics: 97\nTECHNICAL SKILLS\nProgramming Languages: Python (Advanced), C++ (DSA Proficient)\nCurrently Learning: TensorFlow, PyTorch\nStrong Knowledge: Scikit-learn, Machine Learning, Data Processing, Statistical Analysis\nTools & Platforms: Jupyter Notebook, Visual Studio Code, Git/GitHub, DWSIM\nLearning: Computer Vision\nLanguages: English (Fluent), Urdu (Native), Hindi (Native)\nRESEARCH & PROJECTS\nDWSIM Surrogate Modelling - Independent Project\nSelf-Initiated Research | 2026\n• Developed machine learning surrogate model for complex DWSIM simulations\n• Extracted data via Python NET interface, trained multiple models with ANN achieving highest accuracy\n• Successfully captured physical relationships between input-output parameters\n• GitHub: github.com/Mo-Sahil-AI/DWSIM-surrogate-model\nFoundational Models for Medical Imaging - Research Project\nZakir Husain College of Engineering and Technology | 2026 - Present\n• Joining foundational models project for medical imaging with senior researchers\n• Working with diverse medical data including 3D images, 2D images, and sequential chromosomal data using\ntransfer learning techniques\nTRAINING & CERTIFICATIONS\nHarvard's CS50P - Python Programming\n• Completed comprehensive course with hands-on projects\nIIRS - AI/ML for Geospatial Data\n• Advanced training in machine learning for geospatial imagery analysis\n• Topics: Image processing, noise handling, contrast enhancement, computer vision techniques\n• Merit Certificate anticipated upon completion\nWORKSHOPS\nPixels to Prediction - AI Workshop on Image Classification\n2-Day Intensive Workshop | 2026\n• Focused training on image classification techniques and practical AI applications\nTransformers - A Generative AI Workshop\n3-Day Intensive Workshop | 2026\n• Advanced study of transformer architecture and generative AI concepts\nbe10X - AI Tools for Productivity Workshop\nComprehensive EdTech Workshop | 2026\n• Mastered practical AI tools and applications for enhancing work productivity and efficiency\n• Tools covered: NotebookLM, Whispr Flow AI, and emerging AI productivity platforms\nACHIEVEMENTS\n• IMOCSEA Bronze Medal - International Mathematics Olympiad Competition Southeast Asia | Advanced\nmathematical problem-solving\n• Learned and Completed Machine Learning at Its Core - Strong foundation through hands-on projects and\npractical experience\n• Practical AI Tools Expertise - Comprehensive training in modern AI productivity tools and their applications\n• Consistent Academic Excellence - A+ grades in quantitative and technical coursework\n• Self-Directed Learning - Completed multiple advanced courses and certifications independently\n• Research Initiative - Actively engaged in university-level research projects with senior mentors	b0f1fa914ae2f55d0f08c29a350995a2763a0694d795e6638e4332852870886c	2026-10-30 10:52:38.192495
8ae5de1c-dfb3-41ed-ad11-490dc46ec0f9	897955fe-f0e4-44c3-a4c9-04340cc8e9e7	1	MITACS_CV_Final_Mo_Sahil (1).pdf	MO SAHIL\nAI/ML Research Intern\nAligarh, Uttar Pradesh | +91-7355378953 | kas2029.mohammedsahil@gmail.com\nGitHub: github.com/Mo-Sahil-AI | LinkedIn: linkedin.com/in/mo-sahil-6903803a0 | Google Dev: g.dev/mosahil\nEDUCATION\nB.Tech Computer Engineering (Artificial Intelligence)\nZakir Husain College of Engineering and Technology, AMU | July 2025 - Present\nCGPA: 9.151/10 • A+ Grades: Applied Mathematics I & II, Python Programming Lab, Applied Chemistry, Principles of\nElectronics Engineering\nSenior Secondary (Class 12)\nSaiyyid Hamid Senior Secondary School, Aligarh | 2025\nScore: 94.4% • Computer Science: 97 • Mathematics: 97\nTECHNICAL SKILLS\nProgramming Languages: Python (Advanced), C++ (DSA Proficient)\nCurrently Learning: TensorFlow, PyTorch\nStrong Knowledge: Scikit-learn, Machine Learning, Data Processing, Statistical Analysis\nTools & Platforms: Jupyter Notebook, Visual Studio Code, Git/GitHub, DWSIM\nLearning: Computer Vision\nLanguages: English (Fluent), Urdu (Native), Hindi (Native)\nRESEARCH & PROJECTS\nDWSIM Surrogate Modelling - Independent Project\nSelf-Initiated Research | 2026\n• Developed machine learning surrogate model for complex DWSIM simulations\n• Extracted data via Python NET interface, trained multiple models with ANN achieving highest accuracy\n• Successfully captured physical relationships between input-output parameters\n• GitHub: github.com/Mo-Sahil-AI/DWSIM-surrogate-model\nFoundational Models for Medical Imaging - Research Project\nZakir Husain College of Engineering and Technology | 2026 - Present\n• Developing foundational models for diverse medical imaging applications with senior researchers\n• Working with multiple data modalities: 3D medical images, 2D images, sequential chromosomal data\n• Focus: Transfer learning and domain-specific model adaptation strategies\nTRAINING & CERTIFICATIONS\nHarvard's CS50P - Python Programming\n• Completed comprehensive course with hands-on projects\nIIRS - AI/ML for Geospatial Data\n• Advanced training in machine learning for geospatial imagery analysis\n• Topics: Image processing, noise handling, contrast enhancement, computer vision techniques\nGoogle Cloud Skills Program\n• Active Participant: Google Cloud Arcade Facilitator Program\n• Skills Earned: Cloud Infrastructure, Databases, Data Analytics • Profile: g.dev/mosahil\nWORKSHOPS\nPixels to Prediction - AI Workshop on Image Classification\n2-Day Intensive Workshop | 2026\n• Focused training on image classification techniques and practical AI applications\nTransformers - A Generative AI Workshop\n3-Day Intensive Workshop | 2026\n• Advanced study of transformer architecture and generative AI concepts\nbe10X - AI Tools for Productivity Workshop\nComprehensive EdTech Workshop | 2026\n• Mastered practical AI tools and applications for enhancing work productivity and efficiency\n• Tools covered: NotebookLM, Whispr Flow AI, and emerging AI productivity platforms\n• Focus: Real-world application of AI for automating tasks, generating insights, and boosting performance\nPROFESSIONAL EXPERIENCE\nOnline Mathematics & Programming Tutor\nSelf-Employed / In Progress | 2026 onwards\n• Teaching Mathematics and Programming online to students globally\n• Focus areas: Data Structures, Algorithms, Applied Mathematics, Python Programming\nACHIEVEMENTS\n• IMOCSEA Bronze Medal - International Mathematics Olympiad Competition Southeast Asia | Advanced\nmathematical problem-solving\n• Learned and Completed Machine Learning at Its Core - Strong foundation through hands-on projects and\npractical experience\n• Practical AI Tools Expertise - Comprehensive training in modern AI productivity tools and their applications\n• Consistent Academic Excellence - A+ grades in quantitative and technical coursework\n• Self-Directed Learning - Completed multiple advanced courses and certifications independently\n• Research Initiative - Actively engaged in university-level research projects with senior mentors	dab7852b7e3e26d27f076cbaf63c58b576bfc2e41d6b4dd34ceceef8b7119218	2026-10-30 11:28:20.196952
eafc2377-467a-4ce6-a0ad-2047caa88996	897955fe-f0e4-44c3-a4c9-04340cc8e9e7	2	Updated_Resume.pdf	MO SAHIL\nAligarh, Uttar Pradesh 202002 | +91-7355378953 | kas2029.mohammedsahil@gmail.com\nGitHub: github.com/Mo-Sahil-AI | Google Developer: g.dev/mosahil\nEDUCATION\nComputer Engineering (Artificial Intelligence), B.Tech\nJuly 2025 - Present\nZakir Husain College of Engineering and Technology, AMU, Aligarh\nCGPA: 9.151/10\nA+ grades in: Applied Mathematics I & II | Python Programming Lab | Applied Chemistry | Principles of\nElectronics Engineering\n12th Standard | BSSSE Board, AMU\n2025\nSaiyyid Hamid Senior Secondary School, Aligarh\n94.4%\nComputer Science: 97 | Mathematics: 97\nTECHNICAL SKILLS\nProgramming\nPython (Advanced), C++ (DSA proficient)\nML/AI Frameworks\nTensorFlow, Scikit-learn, PyTorch (learning)\nCloud & Tools\nGoogle Cloud Platform, DWSIM, Jupyter Notebook, Git/GitHub\nCore Competencies\nMachine Learning, Data Structures & Algorithms, Computer Vision, Statistical Analysis\nPROJECTS & RESEARCH\nDWSIM Surrogate Modelling - Applied Research Project\n• Developed a machine learning-based surrogate model for DWSIM simulation process optimization\n• Applied advanced regression techniques to reduce computational time while maintaining accuracy\n• GitHub: DWSIM-surrogate-model\nMedical Imaging - DaT Parkinson's Challenge\n• Participating in competitive ML challenge for Parkinson's disease detection using medical imaging data\n• Implementing computer vision techniques and deep learning models for diagnostic accuracy\n• Challenge: DaT Parkinson's Challenge\nFoundational Model Research - Medical Imaging\n• Preparing for research project on developing foundational models for medical imaging applications\n• Focus on transfer learning: adapting general domain models for specialized medical imaging tasks\n• Exploring architecture design and fine-tuning strategies for domain-specific adaptation\nCERTIFICATIONS & ACHIEVEMENTS\nHarvard's CS50P - Introduction to Programming with Python\nCompleted comprehensive course with practical projects | GitHub: CS50P Projects\nGoogle Cloud Skills & Arcade Program\n• Active participant in Google Cloud Arcade Facilitator Program\n• Earned multiple Google Skill Badges across cloud infrastructure, databases, and data analytics\n• Developer Profile: g.dev/mosahil\nInternational Mathematics Olympiad Competition Southeast Asia (IMOCSEA)\n• Bronze Medal recipient - demonstrated advanced problem-solving and mathematical reasoning\nAREAS OF INTEREST\nMachine Learning & Artificial Intelligence • Deep Learning • Computer Vision • Data Science • Research &\nDevelopment • Model Architecture Design • Transfer Learning • Medical AI Applications • Problem Solving &\nAlgorithm Optimization	f1e4c1d3b3c4edfaec3a64a441d37dc2b47d6ee01b02e218f45488ca3c149a87	2026-10-30 11:29:32.264229
7dbefdba-82b1-419b-8686-bd42d410d658	33ffc80d-c49f-4232-81be-dfbeb630cbe7	2	Updated_Resume.pdf	MO SAHIL\nAligarh, Uttar Pradesh 202002 | +91-7355378953 | kas2029.mohammedsahil@gmail.com\nGitHub: github.com/Mo-Sahil-AI | Google Developer: g.dev/mosahil\nEDUCATION\nComputer Engineering (Artificial Intelligence), B.Tech\nJuly 2025 - Present\nZakir Husain College of Engineering and Technology, AMU, Aligarh\nCGPA: 9.151/10\nA+ grades in: Applied Mathematics I & II | Python Programming Lab | Applied Chemistry | Principles of\nElectronics Engineering\n12th Standard | BSSSE Board, AMU\n2025\nSaiyyid Hamid Senior Secondary School, Aligarh\n94.4%\nComputer Science: 97 | Mathematics: 97\nTECHNICAL SKILLS\nProgramming\nPython (Advanced), C++ (DSA proficient)\nML/AI Frameworks\nTensorFlow, Scikit-learn, PyTorch (learning)\nCloud & Tools\nGoogle Cloud Platform, DWSIM, Jupyter Notebook, Git/GitHub\nCore Competencies\nMachine Learning, Data Structures & Algorithms, Computer Vision, Statistical Analysis\nPROJECTS & RESEARCH\nDWSIM Surrogate Modelling - Applied Research Project\n• Developed a machine learning-based surrogate model for DWSIM simulation process optimization\n• Applied advanced regression techniques to reduce computational time while maintaining accuracy\n• GitHub: DWSIM-surrogate-model\nMedical Imaging - DaT Parkinson's Challenge\n• Participating in competitive ML challenge for Parkinson's disease detection using medical imaging data\n• Implementing computer vision techniques and deep learning models for diagnostic accuracy\n• Challenge: DaT Parkinson's Challenge\nFoundational Model Research - Medical Imaging\n• Preparing for research project on developing foundational models for medical imaging applications\n• Focus on transfer learning: adapting general domain models for specialized medical imaging tasks\n• Exploring architecture design and fine-tuning strategies for domain-specific adaptation\nCERTIFICATIONS & ACHIEVEMENTS\nHarvard's CS50P - Introduction to Programming with Python\nCompleted comprehensive course with practical projects | GitHub: CS50P Projects\nGoogle Cloud Skills & Arcade Program\n• Active participant in Google Cloud Arcade Facilitator Program\n• Earned multiple Google Skill Badges across cloud infrastructure, databases, and data analytics\n• Developer Profile: g.dev/mosahil\nInternational Mathematics Olympiad Competition Southeast Asia (IMOCSEA)\n• Bronze Medal recipient - demonstrated advanced problem-solving and mathematical reasoning\nAREAS OF INTEREST\nMachine Learning & Artificial Intelligence • Deep Learning • Computer Vision • Data Science • Research &\nDevelopment • Model Architecture Design • Transfer Learning • Medical AI Applications • Problem Solving &\nAlgorithm Optimization	f1e4c1d3b3c4edfaec3a64a441d37dc2b47d6ee01b02e218f45488ca3c149a87	2026-11-07 21:51:10.272052
4ae5beb9-a84a-4f3c-865d-f1a511458498	d15bda3f-2d1b-48b3-8838-078c2593879b	1	LOR_MITACS_Globalink_Mo_Sahil.pdf	Department of Computer Engineering\nZakir Husain College of Engineering and Technology\nAligarh Muslim University\nAligarh, Uttar Pradesh 202002, India\n[Date]\nTo the MITACS Globalink Internship Selection Committee,\nI write this letter in strong support of Mo Sahil, a second-year student pursuing Bachelor of\nTechnology in Computer Engineering (Artificial Intelligence) at Zakir Husain College of\nEngineering and Technology, Aligarh Muslim University. Mo Sahil has been a student in my\nData Structures and Algorithms course since August 2026. Based on his coursework\nperformance, project initiatives, and demonstrated interest in research, I believe he is a\nwell-qualified candidate for the MITACS Globalink Research Internship program.\nMo Sahil maintains a strong academic record with a current CGPA of 9.151 and A+ grades in\ncore quantitative courses including Applied Mathematics I and II. These results demonstrate\nsolid competency in mathematical and analytical foundations necessary for technical\nresearch. His performance in Data Structures and Algorithms reflects good understanding of\nalgorithmic design, complexity analysis, and implementation techniques. He engages\nmeaningfully with course material and shows capability in applying theoretical concepts to\npractical problem-solving.\nMo Sahil has taken active steps to apply his knowledge beyond coursework. He has\ncompleted a DWSIM surrogate modelling project, demonstrating his ability to work with\ndomain-specific computational tools. He is currently participating in a medical imaging\ncomputer vision competition, where he is applying machine learning techniques to real\ndiagnostic challenges. Most notably, when I discussed potential research directions with him,\nhe expressed clear interest in working on a research project involving foundational models for\nmedical imaging. He understands the concept of adapting general models for specialized\napplications, which indicates constructive thinking about research methodology.\nMo Sahil possesses the technical capabilities required for research work. He has\ndemonstrated strong proficiency in Python through his completion of Harvard's CS50P course\nand possesses working knowledge of C++ for Data Structures implementation. He is actively\nlearning machine learning frameworks and has engaged with Google Cloud Platform tools\nthrough structured programs. His GitHub repository contains evidence of project work and\ncode management practices. These capabilities provide a solid technical foundation for\nresearch-oriented work.\nBased on our interactions, Mo Sahil demonstrates qualities important for research success.\nHe asks thoughtful questions about research directions and shows genuine curiosity about\nhow theoretical concepts apply to practical problems. He has taken initiative to explore\nresearch topics independently, seeking guidance on appropriate next steps in advanced\ntechnical areas. He demonstrates the ability to work systematically on complex problems and\nshows willingness to engage with unfamiliar material. These traits suggest he can adapt to a\nresearch environment and work effectively with mentorship.\nI recommend Mo Sahil for the MITACS Globalink Research Internship program. His academic\nfoundation is solid, his technical skills are developing appropriately, and his interest in\nresearch is genuine. I am confident he will work productively as a research intern and will\nbenefit significantly from the opportunity to engage in international collaborative research. He\nrepresents a capable student ready to contribute to meaningful research work.\nYours sincerely,\nDr. Nadeem Akhtar\nAssistant Professor\nDepartment of Computer Engineering\nZakir Husain College of Engineering and Technology\nAligarh Muslim University, Aligarh\nEmail: [Professor Email]\nPhone: +91-[Professor Phone]	5230eb5321985b4dfefd3b8a79df7b1c17d95d7255f9f2a897290995bf97175a	2026-11-07 21:52:50.997794
\.


--
-- Data for Name: user_profile; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_profile (user_id, current_resume_id, current_resume_version, current_jd_id, current_jd_version, current_analysis_id, current_analysis_version, updated_at) FROM stdin;
897955fe-f0e4-44c3-a4c9-04340cc8e9e7	eafc2377-467a-4ce6-a0ad-2047caa88996	2	3bb6c927-69ab-4bbf-85c6-a163d7193d03	1	f08b2a1d-3010-4408-a9fe-fb966ef37830	2	2026-10-30 11:28:20.351594
33ffc80d-c49f-4232-81be-dfbeb630cbe7	7dbefdba-82b1-419b-8686-bd42d410d658	2	bd9ee2a7-e10a-488c-a861-6b71d8bb83b3	3	74f3dd05-b046-49a3-a088-5009890d71f1	4	2026-10-30 10:52:38.799218
d15bda3f-2d1b-48b3-8838-078c2593879b	4ae5beb9-a84a-4f3c-865d-f1a511458498	1	6012089c-d183-4ccc-9dd7-c23b03bb08eb	1	88797ef1-5a06-4830-8cff-ca56bf476881	1	2026-11-07 21:52:51.076514
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, email, created_at, password_hash) FROM stdin;
33ffc80d-c49f-4232-81be-dfbeb630cbe7	sahil@gmail.com	2026-10-30 10:51:10.193709	$argon2id$v=19$m=65536,t=3,p=4$ko/6Pi+pLCnYfA/5Kr52gw$BTCqsfAF93rY0n0gkMl9ZZZ3H0Q8SRlXyEm0016aWm8
897955fe-f0e4-44c3-a4c9-04340cc8e9e7	kas20@gmail.com	2026-10-30 11:27:09.306987	$argon2id$v=19$m=65536,t=3,p=4$o3bvssBPz7adJhVAUQs7gA$LT5qqDlBmq+nROg2O75iyyl+2zmFy5TNLDFFMtNuB60
d15bda3f-2d1b-48b3-8838-078c2593879b	ali@gmail.com	2026-11-07 21:49:17.199955	$argon2id$v=19$m=65536,t=3,p=4$Yvh7dPAnGajDekb3mNEWyw$pKOMPhewaDq6XFJe13NmkfF6DqPBs3qqJRFiZrwrp/E
\.


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
-- PostgreSQL database dump complete
--

\unrestrict v6xtLMu5YW9FTEbYpxnSEk9nKTfCWzjTiwbrw7JiAaoRadPgKhEf2rVdJILyDXV

