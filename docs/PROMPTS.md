# Prompts & Planning

This document captures the prompts used during the development of this Incident Management System. The assignment requires that "all markdowns and prompts used to create this repository should be checked in."

---

## Initial Scoping Prompt

The very first prompt was a scoping conversation — *not* a code-generation prompt — used to validate feasibility, clarify the assignment language, and decide on a tech stack before writing any code.

The full prompt sent (along with the job description, the assignment PDF, and a copy of the recruiter email) is reproduced below verbatim.

> I have been shared an assignment as part of the application process. Here is the job description:
>
> ---
>
> **Infrastructure / SRE Intern — Hybrid Bangalore (India, Karnātaka, Bangalore)**
>
> **About Zeotap**
>
> Founded in Berlin in 2014, Zeotap started with a mission to provide high-quality data to marketers. As we evolved, we recognized a greater challenge: helping brands create personalized, multi-channel experiences in a world that demands strict data privacy and compliance. This drive led to the launch of Zeotap's Customer Data Platform (CDP) in 2020 — a powerful, AI-native SaaS suite built on Google Cloud that empowers brands to unlock and activate customer data securely.
>
> Today, Zeotap is trusted by some of the world's most innovative brands, including Virgin Media O2, Amazon, and Audi, to create engaging, data-driven customer experiences that drive better business outcomes across marketing, sales, and service. With a unique background in high-quality data solutions, Zeotap is a leader in the European CDP market, empowering enterprises with a secure, privacy-first solution to harness the full potential of their customer data. Zeotap is expanding its SaaS product suites branded as Customer Intelligence Platform consisting of an integrated product suite for Customer data collection, ID resolution, Predictive Analytics, Audience management.
>
> **Responsibilities:**
>
> - You diagnose GKE clusters with stuck on-demand nodes costing ~$1,770/month, correct scheduling policies, and safely drain nodes across five clusters in a single coordinated session.
> - You build Spendrift, an internal cost-intelligence platform (Python, FastAPI, React, BigQuery) that detects billing anomalies, forecasts cloud spend, and automatically surfaces waste.
> - You investigate an 878% spike in GCS API usage at 10pm, trace it to a specific bucket and job, and determine whether it is legitimate activity or a false alarm.
> - You design and maintain infrastructure automation using Terraform, Helm charts, CI/CD pipelines, and GitOps workflows to ensure reliable, repeatable deployments.
> - You implement and debug security and IAM controls, including Workload Identity, Credential Access Boundaries, SAML/SSO integrations, and Kubernetes network policies.
> - You build AI-powered tooling and agent platforms leveraging LLMs for infrastructure validation, alert triage, and automated operational reporting.
> - You adhere to Zeotap's company, privacy and information security policies and procedures.
> - You complete all the awareness training assigned on time.
>
> *Most internships give you a sandbox. This one gives you production.*
>
> **Requirements**
>
> *Must Have:*
> - Strong Linux fundamentals
> - Kubernetes — you understand pods, scheduling, services, namespaces
> - Cloud basics — VPCs, IAM, storage tiers, compute models. GCP preferred, AWS is fine
> - Python or Go
> - Networking — DNS, load balancers, TCP/IP, firewalls
> - Git — branching, rebasing, PRs
>
> *Good to have:*
> - Terraform or any IaC experience
> - Docker
> - Monitoring/observability (Prometheus, Grafana, Cloud Monitoring)
> - Contributed to open source or have a side project with real users
> - You've broken something in production and learned from it
>
> ---
>
> I have also attached my resume for reference.
>
> Also attaching the assignment doc, and sharing below the mail received:
>
> ---
>
> **Assignment | Infrastructure / SRE Intern | Zeotap**
>
> *Karan Kenny Sinha &lt;karan.kenny@zeotap.recruitee.com&gt;*
>
> Dear Afzaal,
>
> Thanks for showing interest in the Infrastructure / SRE Intern position at Zeotap. As a next step in the hiring process, we'd like to share an assignment with you. This will help us better understand your approach, problem-solving skills, and alignment with the role.
>
> *Instructions for the assignment:*
>
> - This is an open-book test. So assignment takers are free to use any GPT tool of their choice.
> - The first qualification criteria is a running application. So ensure the readme and packaging are correct and you test it.
> - GitHub usage is mandatory and codebase/build scripts/configs are to be present there.
> - Any non-functional items taken care of like adding security layer, performance etc please add in the readme. These earn you bonus points.
> - Assignment should be submitted in one pdf.
> - The pdf file should be named in the following format: `Full Name - Infrastructure / SRE Intern Assignment`.
> - Mandatory — Kindly add the GitHub link to the pdf.
> - The deadline for submission is 6th May 2026.
> - The candidates have to submit their completed assignment to karan.sinha@zeotap.com.
>
> We appreciate the time and effort you'll be putting into this and look forward to reviewing your submission.
>
> Regards,
> Talent Team, Zeotap
> — Karan Kenny Sinha
>
> ---
>
> As you can see, the submission deadline is 6th May, 2026 and today is 30 Apr, 2026. I have a few quick questions, before we move ahead and start working/coding on this project/assignment.
>
> 1. Is it feasible to complete in the duration?
> 2. I have a basic/broad understanding, but not completely getting the terms, and the real ask of the assignment, can you please explain in much detail, and also what technologies will be ideal to use here and why (keeping in mind, the ask and that we want to complete and crack this job).
> 3. How do we proceed and why? What steps matter first, why, what are the things to look out for, etc. I am very much open to learning and improve on the way, but I want this project to be a 10/10 meeting the standards and not compromising. I will give my best, but I want to first completely understand, all the simple and all the complex things.
> 4. What are the submission requirements, I am finding the 4th point in the submission guidelines of the assignment pdf confusing, what is the ask there?

---

## How This Prompt Shaped the Project

The output of this scoping conversation drove every major decision that followed:

| Question | Decision That Resulted |
|---|---|
| Feasibility in 6 days | Timeboxed scope: prioritise the rubric (concurrency, data handling, LLD, UI, resilience, docs, tech stack) over breadth. Defer multi-worker scaling, Alembic migrations, and full integration test suites to the roadmap. |
| Real ask of the assignment | Mapped each assignment phrase ("Producer", "Sink", "Hot-Path", "State Pattern", "Strategy Pattern") to a concrete component before writing code. |
| Ideal technologies | Python + FastAPI for async ingestion, PostgreSQL as transactional source of truth, MongoDB for raw signal data lake + timeseries, Redis for debounce + dashboard cache, React for the UI, Docker Compose to make the "running application" qualification trivial. Rationale captured in [`ARCHITECTURE.md`](ARCHITECTURE.md). |
| How to proceed | Build storage and async ingestion first, then the workflow engine (State + Strategy patterns), then the frontend, then docs and tests. The rubric weights were used as the prioritisation key. |
| Submission point #4 ("Prompts/Spec/Plans") | This file. Plus [`DESIGN_PATTERNS.md`](DESIGN_PATTERNS.md) and [`ARCHITECTURE.md`](ARCHITECTURE.md). |

---

## Subsequent Prompts

After the scoping conversation, the rest of development was driven by short, focused prompts against the codebase — implementing one component at a time (ingestion endpoint, queue + worker, debouncer, state machine, RCA model and validation, alert strategy registry, frontend pages, tests). These were iterative coding prompts against the live repository rather than standalone planning prompts, so they are not reproduced here individually; the resulting code, commit history, and design docs are the artefact.

The final review of the repository against the assignment rubric was driven by an audit prompt that produced the gap list (missing `PROMPTS.md`, missing `ARCHITECTURE.md`, README clarifications around single-worker scope and deferred CORS work, explicit "Bonus / Creative Additions" callout). This document is one of the outcomes of that audit.
