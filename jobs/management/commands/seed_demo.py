from django.core.management.base import BaseCommand
from accounts.models import User
from students.models import Skill, StudentProfile, StudentSkill
from companies.models import Company
from recruiters.models import RecruiterProfile
from jobs.models import Job
from django.utils import timezone
import datetime


class Command(BaseCommand):
    help = 'Seeds the database with diverse startups, top companies, jobs and demo data for CAMPUSLINK'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding database with top startups, tech companies, and career opportunities...')

        # Core Skills
        skill_names = [
            'Python', 'Django', 'React', 'REST API', 'SQL', 'PostgreSQL', 'Machine Learning',
            'NumPy', 'Pandas', 'Scikit-learn', 'TensorFlow', 'Deep Learning',
            'APIs', 'LLM', 'RAG', 'LangChain', 'AI', 'Cloud', 'Docker', 'Git',
            'Go', 'Java', 'Node.js', 'TypeScript', 'Kubernetes', 'Redis', 'AWS',
            'Flutter', 'Next.js', 'Solidity', 'Rust', 'Kafka', 'FastAPI',
        ]
        skills = {name: Skill.objects.get_or_create(name=name)[0] for name in skill_names}

        # Company catalog: Startups, Unicorns, and Enterprises
        companies_data = [
            {
                'name': 'Sarvam AI',
                'company_type': 'Startup',
                'industry': 'Artificial Intelligence & Indic LLMs',
                'tagline': "Building India's foundational AI and sovereign language models",
                'description': 'Sarvam AI develops full-stack Generative AI foundational models and voice-first interfaces specifically architected for India and Indian enterprise ecosystems.',
                'website': 'https://www.sarvam.ai',
                'locations': 'Bengaluru, Karnataka (Hybrid)',
                'tech_stack': 'Python, PyTorch, CUDA, FastAPI, RAG, LLM',
                'funding_stage': 'Series A ($53M Funded)',
                'employee_count': '40-80 engineers',
                'hiring_process': '1. Technical screening -> 2. System/ML coding interview -> 3. Founder deep-dive discussion',
                'verification_status': 'VERIFIED',
                'open_positions': 3,
                'internship_opportunities': 2,
            },
            {
                'name': 'Krutrim AI',
                'company_type': 'Unicorn',
                'industry': 'AI Cloud & Supercomputing',
                'tagline': "India's first AI unicorn building cloud and compute chips",
                'description': 'Krutrim is building India’s first sovereign AI computing stack, from custom silicon and data centers to large language models and developer APIs.',
                'website': 'https://krutrim.com',
                'locations': 'Bengaluru, Karnataka',
                'tech_stack': 'Python, PyTorch, Ray, Transformers, Go, Kubernetes',
                'funding_stage': 'Unicorn ($1B+ Valuation)',
                'employee_count': '150-300 engineers',
                'hiring_process': '1. Hackathon/Code assessment -> 2. Distributed ML architecture -> 3. Hiring manager round',
                'verification_status': 'VERIFIED',
                'open_positions': 4,
                'internship_opportunities': 1,
            },
            {
                'name': 'CRED',
                'company_type': 'Unicorn',
                'industry': 'FinTech & High-Trust Ecosystem',
                'tagline': 'Crafting reward-driven financial products for high-credit individuals',
                'description': 'CRED is an exclusive community of credit-worthy individuals with cutting-edge mobile interfaces, ultra-low latency transaction systems, and innovative financial rails.',
                'website': 'https://cred.club',
                'locations': 'Bengaluru, Karnataka',
                'tech_stack': 'Java, Go, Kafka, React, PostgreSQL, Docker',
                'funding_stage': 'Unicorn ($6.4B Valuation)',
                'employee_count': '500-1000 employees',
                'hiring_process': '1. Machine coding round -> 2. High-scale architecture design -> 3. Culture & values interview',
                'verification_status': 'VERIFIED',
                'open_positions': 4,
                'internship_opportunities': 2,
            },
            {
                'name': 'Razorpay',
                'company_type': 'Unicorn',
                'industry': 'Payment Gateway & Neo-Banking',
                'tagline': 'Powering payments and financial automation for modern businesses',
                'description': 'Razorpay enables millions of businesses to accept, process and disburse digital payments with developer-friendly APIs and high reliability.',
                'website': 'https://razorpay.com',
                'locations': 'Bengaluru, Karnataka (Hybrid)',
                'tech_stack': 'Go, Python, AWS, MySQL, Redis, Kafka',
                'funding_stage': 'Unicorn ($7.5B Valuation)',
                'employee_count': '1,500+ employees',
                'hiring_process': '1. Online coding round -> 2. Data structures & API design -> 3. Engineering bar raiser',
                'verification_status': 'VERIFIED',
                'open_positions': 3,
                'internship_opportunities': 1,
            },
            {
                'name': 'Zepto',
                'company_type': 'Unicorn',
                'industry': 'Quick Commerce & Supply Chain',
                'tagline': '10-minute grocery and essentials delivery with algorithmic dark stores',
                'description': 'Zepto is India’s fastest-growing quick-commerce tech unicorn, engineering real-time route optimization, predictive demand, and micro-fulfillment automation.',
                'website': 'https://zeptonow.com',
                'locations': 'Mumbai & Bengaluru',
                'tech_stack': 'Go, Python, Next.js, Kubernetes, Redis, Kafka',
                'funding_stage': 'Unicorn ($5B Valuation)',
                'employee_count': '1,200+ employees',
                'hiring_process': '1. Live pair programming -> 2. System design -> 3. Director fit round',
                'verification_status': 'VERIFIED',
                'open_positions': 3,
                'internship_opportunities': 1,
            },
            {
                'name': 'Zerodha',
                'company_type': 'Startup',
                'industry': 'Financial Technology & Capital Markets',
                'tagline': 'Bootstrapped, frugal, and ultra-reliable trading technology',
                'description': 'Zerodha is India’s biggest stockbroker, built on modern open-source software, minimal external dependencies, and ultra-high transaction throughput.',
                'website': 'https://zerodha.tech',
                'locations': 'Bengaluru & Remote',
                'tech_stack': 'Go, Python, PostgreSQL, Redis, Vue, Linux',
                'funding_stage': 'Bootstrapped & Highly Profitable',
                'employee_count': '120 tech team members',
                'hiring_process': '1. Open-source contribution review -> 2. Practical problem solving -> 3. Tech lead chat',
                'verification_status': 'VERIFIED',
                'open_positions': 2,
                'internship_opportunities': 1,
            },
            {
                'name': 'Postman',
                'company_type': 'Unicorn',
                'industry': 'Developer Tools & API Infrastructure',
                'tagline': "The world's leading API platform used by 30M+ developers",
                'description': 'Postman simplifies each step of the API lifecycle and streamlines collaboration so you can create better APIs faster.',
                'website': 'https://www.postman.com',
                'locations': 'Bengaluru / Remote',
                'tech_stack': 'TypeScript, Node.js, React, Go, Docker, AWS',
                'funding_stage': 'Unicorn ($5.6B Valuation)',
                'employee_count': '1,000+ employees',
                'hiring_process': '1. Take-home project/API exercise -> 2. Technical deep-dive -> 3. Cross-functional review',
                'verification_status': 'VERIFIED',
                'open_positions': 3,
                'internship_opportunities': 2,
            },
            {
                'name': 'BrowserStack',
                'company_type': 'Unicorn',
                'industry': 'Cloud Testing & DevOps Platform',
                'tagline': 'Instant access to 3,000+ real mobile devices and desktop browsers in cloud',
                'description': 'BrowserStack is the leading software testing platform powering over two million tests every day across 135+ countries.',
                'website': 'https://www.browserstack.com',
                'locations': 'Mumbai / Remote',
                'tech_stack': 'Ruby, Python, Node.js, AWS, Docker, Kubernetes',
                'funding_stage': 'Unicorn ($4B Valuation)',
                'employee_count': '900+ employees',
                'hiring_process': '1. Online assessment -> 2. System design -> 3. Engineering leadership round',
                'verification_status': 'VERIFIED',
                'open_positions': 2,
                'internship_opportunities': 1,
            },
            {
                'name': 'Groww',
                'company_type': 'Unicorn',
                'industry': 'WealthTech & Investment Platform',
                'tagline': 'Making investing transparent, simple, and accessible for everyone',
                'description': 'Groww provides a frictionless platform for direct mutual funds, stocks, US investments, and gold to millions of Indian retail investors.',
                'website': 'https://groww.in',
                'locations': 'Bengaluru, Karnataka',
                'tech_stack': 'Java, Spring Boot, React, Kafka, PostgreSQL, AWS',
                'funding_stage': 'Unicorn ($3B Valuation)',
                'employee_count': '1,000+ employees',
                'hiring_process': '1. Coding assessment -> 2. Low-level design -> 3. Cultural alignment',
                'verification_status': 'VERIFIED',
                'open_positions': 3,
                'internship_opportunities': 1,
            },
            {
                'name': 'Urban Company',
                'company_type': 'Unicorn',
                'industry': 'Marketplace & At-Home Services',
                'tagline': "Asia's largest home services marketplace tech platform",
                'description': 'Urban Company empowers over 50,000 service partners using smart matchmaking, dynamic scheduling algorithms, and end-to-end customer apps.',
                'website': 'https://www.urbancompany.com',
                'locations': 'Gurgaon, Haryana (Hybrid)',
                'tech_stack': 'Python, Node.js, React, Next.js, Kafka, AWS',
                'funding_stage': 'Unicorn ($2.8B Valuation)',
                'employee_count': '1,200+ employees',
                'hiring_process': '1. Data structures challenge -> 2. System design -> 3. Tech VP round',
                'verification_status': 'VERIFIED',
                'open_positions': 2,
                'internship_opportunities': 1,
            },
            {
                'name': 'Polygon Labs',
                'company_type': 'Startup',
                'industry': 'Web3 & Zero-Knowledge Cryptography',
                'tagline': 'Building the value layer of the Internet through zero-knowledge Ethereum scaling',
                'description': 'Polygon develops zero-knowledge cryptographic tech and high-throughput blockchain networks, enabling global Web3 mass adoption.',
                'website': 'https://polygon.technology',
                'locations': 'Remote (Global)',
                'tech_stack': 'Go, Rust, Solidity, TypeScript, Docker',
                'funding_stage': 'High-Growth Web3 Unicorn',
                'employee_count': '350+ engineers worldwide',
                'hiring_process': '1. Cryptographic/System task -> 2. Protocol architecture -> 3. Team lead interview',
                'verification_status': 'VERIFIED',
                'open_positions': 2,
                'internship_opportunities': 1,
            },
            {
                'name': 'Microsoft India',
                'company_type': 'Enterprise',
                'industry': 'Cloud, OS & Enterprise AI',
                'tagline': 'Empowering every person and organization on the planet to achieve more',
                'description': 'Microsoft India IDC is one of Microsoft’s premier engineering centers, creating mission-critical products for Azure, Windows, Copilot, and Office 365.',
                'website': 'https://www.microsoft.com',
                'locations': 'Hyderabad & Bengaluru',
                'tech_stack': 'C#, Python, Azure, TypeScript, PyTorch, Docker',
                'funding_stage': 'Global Enterprise MNC',
                'employee_count': '18,000+ in India',
                'hiring_process': '1. Campus/Online test -> 2. Technical interviews (DS/Algo) -> 3. As-Appropriate (AA) round',
                'verification_status': 'VERIFIED',
                'open_positions': 4,
                'internship_opportunities': 2,
            },
            {
                'name': 'Google Cloud India',
                'company_type': 'Enterprise',
                'industry': 'Global Cloud & Distributed Systems',
                'tagline': 'Organizing the world’s information and making it universally accessible',
                'description': 'Google India engineering teams build high-scale solutions across Google Cloud, Kubernetes, Android, and next-generation AI infrastructure.',
                'website': 'https://cloud.google.com',
                'locations': 'Bengaluru & Hyderabad',
                'tech_stack': 'Go, Python, GCP, Kubernetes, Java, TensorFlow',
                'funding_stage': 'Global Enterprise MNC',
                'employee_count': '10,000+ in India',
                'hiring_process': '1. Technical telephone round -> 2. Onsite/virtual DS & Algo rounds -> 3. Googliness interview',
                'verification_status': 'VERIFIED',
                'open_positions': 3,
                'internship_opportunities': 2,
            },
            {
                'name': 'TCS Digital',
                'company_type': 'Enterprise',
                'industry': 'Digital Transformation & Enterprise Engineering',
                'tagline': 'Pioneering digital solutions and next-generation consulting across 50+ countries',
                'description': 'TCS Digital is the advanced technology unit of Tata Consultancy Services, focusing on AI, Cloud, IoT, and high-performance computing.',
                'website': 'https://www.tcs.com',
                'locations': 'Bhubaneswar, Odisha & Pune',
                'tech_stack': 'Java, Python, Cloud, Spring, PostgreSQL, Docker',
                'funding_stage': 'Tata Group Enterprise',
                'employee_count': '600,000+ global workforce',
                'hiring_process': '1. National Qualifier Test (NQT) -> 2. Technical interview -> 3. HR interview',
                'verification_status': 'VERIFIED',
                'open_positions': 5,
                'internship_opportunities': 3,
            },
            {
                'name': 'Tech Innovations Inc.',
                'company_type': 'Product Lab',
                'industry': 'Enterprise AI Platforms',
                'tagline': 'Applied machine intelligence and cognitive automation products',
                'description': 'Tech Innovations Inc. is a high-growth product studio building enterprise workflow copilots, document intelligence, and real-time streaming pipelines.',
                'website': 'https://techinnovations.example.com',
                'locations': 'Bhubaneswar & Pune',
                'tech_stack': 'Python, Django, React, REST API, PostgreSQL, AI',
                'funding_stage': 'Series B / Growth',
                'employee_count': '180 engineers',
                'hiring_process': '1. Coding round -> 2. System design -> 3. Director interview',
                'verification_status': 'VERIFIED',
                'open_positions': 4,
                'internship_opportunities': 2,
            },
        ]

        companies = {}
        for cdata in companies_data:
            comp, created = Company.objects.update_or_create(
                name=cdata['name'],
                defaults=cdata,
            )
            companies[cdata['name']] = comp

        # Users and profiles setup
        student_user, _ = User.objects.get_or_create(username="student1", defaults={"email": "student1@example.com", "role": "STUDENT"})
        student_user.set_password("password123")
        student_user.save()

        bapuni_user, _ = User.objects.get_or_create(
            username="bapuni_123",
            defaults={"email": "bapuni_123@example.com", "role": "STUDENT"},
        )
        bapuni_user.role = "STUDENT"
        bapuni_user.set_password("Bapuni@123")
        bapuni_user.save()

        recruiter_user, _ = User.objects.get_or_create(username="recruiter1", defaults={"email": "recruiter@example.com", "role": "RECRUITER"})
        recruiter_user.set_password("password123")
        recruiter_user.save()

        officer_user, _ = User.objects.get_or_create(username="officer1", defaults={"email": "officer@example.com", "role": "PLACEMENT_OFFICER"})
        officer_user.set_password("password123")
        officer_user.save()

        student_profile, _ = StudentProfile.objects.get_or_create(
            user=student_user,
            defaults={
                'cgpa': 8.5,
                'graduation_year': 2026,
                'department': 'Computer Science',
                'college': 'BPUT University',
                'phone': '+91 9876543210',
                'location': 'Bhubaneswar, Odisha',
                'degree': 'B.Tech Computer Science & Engineering',
                'headline': 'Aspiring Full Stack & AI Developer | B.Tech CSE',
            }
        )
        StudentSkill.objects.get_or_create(student=student_profile, skill=skills['Python'], defaults={'proficiency': 90})
        StudentSkill.objects.get_or_create(student=student_profile, skill=skills['Django'], defaults={'proficiency': 85})
        StudentSkill.objects.get_or_create(student=student_profile, skill=skills['React'], defaults={'proficiency': 75})
        StudentSkill.objects.get_or_create(student=student_profile, skill=skills['REST API'], defaults={'proficiency': 80})

        bapuni_profile, _ = StudentProfile.objects.get_or_create(
            user=bapuni_user,
            defaults={
                'cgpa': 8.8,
                'graduation_year': 2026,
                'department': 'Computer Science & Engineering',
                'college': 'Biju Patnaik University of Technology (BPUT)',
                'phone': '+91 9439123456',
                'location': 'Bhubaneswar, Odisha',
                'degree': 'B.Tech Computer Science',
                'headline': 'AI & Full Stack Engineer | Python, React, Cloud',
            }
        )
        StudentSkill.objects.get_or_create(student=bapuni_profile, skill=skills['Python'], defaults={'proficiency': 95})
        StudentSkill.objects.get_or_create(student=bapuni_profile, skill=skills['Django'], defaults={'proficiency': 90})
        StudentSkill.objects.get_or_create(student=bapuni_profile, skill=skills['Machine Learning'], defaults={'proficiency': 85})

        RecruiterProfile.objects.get_or_create(
            user=recruiter_user,
            defaults={'company': companies['Sarvam AI'], 'designation': 'Head of Talent Acquisition', 'verified': True}
        )

        # Multi-Company Jobs List
        deadline_30 = timezone.now() + datetime.timedelta(days=30)
        deadline_45 = timezone.now() + datetime.timedelta(days=45)
        deadline_60 = timezone.now() + datetime.timedelta(days=60)
        deadline_90 = timezone.now() + datetime.timedelta(days=90)

        job_catalog = [
            # Sarvam AI
            (
                'AI Research & LLM Engineer',
                'Sarvam AI',
                'Architect, evaluate, and fine-tune large multilingual generative models and tokenizers tailored for Indian enterprise languages. Work on inference optimization and low-latency serving.',
                'Bengaluru, Karnataka',
                '₹18–28 LPA',
                'Full-Time',
                'Hybrid',
                7.5,
                2026,
                ['Python', 'PyTorch', 'LLM', 'RAG', 'Deep Learning', 'FastAPI'],
                deadline_60,
            ),
            (
                'GenAI Applications Intern',
                'Sarvam AI',
                'Collaborate directly with founders and researchers to build voice-agent prototypes, evaluate multi-turn LLM datasets, and test retrieval systems.',
                'Remote',
                '₹45,000 / month',
                'Internship',
                'Remote',
                7.0,
                2026,
                ['Python', 'LangChain', 'APIs', 'RAG', 'Git'],
                deadline_45,
            ),

            # Krutrim AI
            (
                'Machine Learning Systems Engineer',
                'Krutrim AI',
                'Build resilient distributed model training pipelines on custom GPU/NPU clusters. Optimize training throughput, memory utilization, and telemetry.',
                'Bengaluru, Karnataka',
                '₹16–25 LPA',
                'Full-Time',
                'Onsite',
                7.0,
                2026,
                ['Python', 'Machine Learning', 'TensorFlow', 'Deep Learning', 'Docker'],
                deadline_60,
            ),
            (
                'Cloud Backend Engineer (Python/Go)',
                'Krutrim AI',
                'Develop backend APIs and orchestration software for Krutrim Cloud compute instances and model inference endpoints.',
                'Bengaluru, Karnataka',
                '₹14–22 LPA',
                'Full-Time',
                'Hybrid',
                7.0,
                2026,
                ['Python', 'Go', 'Kubernetes', 'REST API', 'PostgreSQL'],
                deadline_60,
            ),

            # CRED
            (
                'SDE-1 Backend Engineer',
                'CRED',
                'Join the high-trust financial engineering team. Build high-throughput microservices handling millions of transactions per second with 99.999% uptime.',
                'Bengaluru, Karnataka',
                '₹16–24 LPA',
                'Full-Time',
                'Onsite',
                7.5,
                2026,
                ['Java', 'Python', 'Go', 'Kafka', 'PostgreSQL', 'Redis'],
                deadline_60,
            ),
            (
                'Full Stack Frontend Engineer',
                'CRED',
                'Craft world-class interactive web and mobile interfaces with smooth animations, high performance, and strict attention to micro-interactions.',
                'Bengaluru, Karnataka',
                '₹14–22 LPA',
                'Full-Time',
                'Onsite',
                7.0,
                2026,
                ['React', 'TypeScript', 'Next.js', 'REST API'],
                deadline_60,
            ),

            # Razorpay
            (
                'Associate Software Engineer (Payments)',
                'Razorpay',
                'Develop secure checkout integrations, automated settlement systems, and fraud prevention pipelines for fast-growing merchants across India.',
                'Bengaluru, Karnataka',
                '₹15–23 LPA',
                'Full-Time',
                'Hybrid',
                7.0,
                2026,
                ['Python', 'Go', 'REST API', 'SQL', 'AWS', 'Docker'],
                deadline_60,
            ),
            (
                'DevOps & Cloud Engineering Intern',
                'Razorpay',
                'Support containerization, CI/CD pipeline automation, automated testing rigs, and multi-region cloud observability.',
                'Remote',
                '₹35,000 / month',
                'Internship',
                'Remote',
                6.5,
                2026,
                ['Cloud', 'Docker', 'Git', 'Python', 'AWS'],
                deadline_45,
            ),

            # Zepto
            (
                'Junior Backend Engineer (Supply Tech)',
                'Zepto',
                'Power 10-minute delivery routing algorithms, dark store inventory reservation engines, and rider fleet management services.',
                'Bengaluru, Karnataka',
                '₹13–21 LPA',
                'Full-Time',
                'Onsite',
                7.0,
                2026,
                ['Go', 'Python', 'Redis', 'PostgreSQL', 'Docker'],
                deadline_60,
            ),
            (
                'Frontend Mobile / Web Engineer',
                'Zepto',
                'Build consumer-facing checkout, search, and live package tracking interfaces with sub-second response times.',
                'Mumbai, Maharashtra',
                '₹12–19 LPA',
                'Full-Time',
                'Hybrid',
                6.5,
                2026,
                ['React', 'TypeScript', 'REST API', 'Git'],
                deadline_60,
            ),

            # Zerodha
            (
                'Python / Go Systems Developer',
                'Zerodha',
                'Work on low-latency trading engines, Kite connect public APIs, and automated regulatory reporting engines using clean, minimalist code.',
                'Remote',
                '₹14–22 LPA',
                'Full-Time',
                'Remote',
                7.0,
                2026,
                ['Python', 'Go', 'PostgreSQL', 'Redis', 'Git'],
                deadline_90,
            ),
            (
                'Web & UI Engineering Intern',
                'Zerodha',
                'Help build accessible, blazing-fast financial web applications and open-source documentation portals for Zerodha Tech.',
                'Remote',
                '₹40,000 / month',
                'Internship',
                'Remote',
                6.5,
                2026,
                ['React', 'TypeScript', 'REST API', 'Python'],
                deadline_45,
            ),

            # Postman
            (
                'API Platform Software Engineer',
                'Postman',
                'Develop core API client features, protocol parsers (REST, GraphQL, gRPC), and collaboration workflows used by 30M+ global developers.',
                'Remote',
                '₹16–26 LPA',
                'Full-Time',
                'Remote',
                7.0,
                2026,
                ['TypeScript', 'Node.js', 'APIs', 'Docker', 'Git'],
                deadline_60,
            ),

            # BrowserStack
            (
                'Cloud Automation & SDET Engineer',
                'BrowserStack',
                'Build resilient automation harnesses and infrastructure drivers to orchestrate device cloud testing across thousands of physical devices.',
                'Mumbai / Remote',
                '₹12–18 LPA',
                'Full-Time',
                'Hybrid',
                6.5,
                2026,
                ['Python', 'Docker', 'Cloud', 'Git', 'REST API'],
                deadline_60,
            ),

            # Groww
            (
                'SDE-1 Backend Services',
                'Groww',
                'Build high-performance microservices for mutual fund ordering, stock trading settlements, and real-time portfolio tracking.',
                'Bengaluru, Karnataka',
                '₹13–20 LPA',
                'Full-Time',
                'Hybrid',
                7.0,
                2026,
                ['Java', 'Python', 'SQL', 'Kafka', 'REST API'],
                deadline_60,
            ),

            # Urban Company
            (
                'Full Stack Developer (Django/React)',
                'Urban Company',
                'Build marketplace partner portals, dynamic dispatch engines, and customer booking web applications with rapid iterative cycles.',
                'Gurgaon, Haryana',
                '₹12–18 LPA',
                'Full-Time',
                'Hybrid',
                6.5,
                2026,
                ['Python', 'Django', 'React', 'REST API', 'SQL'],
                deadline_60,
            ),

            # Polygon Labs
            (
                'Distributed Systems & Web3 Intern',
                'Polygon Labs',
                'Research zero-knowledge rollup proofs, test smart contract execution clients, and benchmark decentralized validator sets.',
                'Remote',
                '₹50,000 / month',
                'Internship',
                'Remote',
                7.5,
                2026,
                ['Go', 'Rust', 'Git', 'Docker', 'APIs'],
                deadline_60,
            ),

            # Microsoft India
            (
                'Software Engineer - Azure Cloud & AI',
                'Microsoft India',
                'Design, implement, and deliver scalable enterprise cloud infrastructure and intelligent services with Microsoft Azure and Copilot teams.',
                'Hyderabad, Telangana',
                '₹20–32 LPA',
                'Full-Time',
                'Hybrid',
                8.0,
                2026,
                ['Python', 'Java', 'Cloud', 'Docker', 'AI', 'Git'],
                deadline_90,
            ),
            (
                'AI Development Intern',
                'Microsoft India',
                'Work alongside principal researchers and engineers on foundation model adaptation, RAG evaluation frameworks, and multimodal services.',
                'Bengaluru, Karnataka',
                '₹60,000 / month',
                'Internship',
                'Hybrid',
                7.5,
                2026,
                ['Python', 'Machine Learning', 'Deep Learning', 'PyTorch', 'Git'],
                deadline_45,
            ),

            # Google Cloud India
            (
                'Cloud Solutions & Distributed Systems Engineer',
                'Google Cloud India',
                'Develop reliable distributed backend systems, Kubernetes-native tooling, and large-scale enterprise cloud solutions.',
                'Bengaluru, Karnataka',
                '₹18–28 LPA',
                'Full-Time',
                'Hybrid',
                8.0,
                2026,
                ['Go', 'Python', 'Kubernetes', 'Cloud', 'SQL', 'Docker'],
                deadline_90,
            ),

            # TCS Digital
            (
                'Digital Software Engineer',
                'TCS Digital',
                'Deliver cutting-edge software development for global Fortune 500 clients in banking, life sciences, and next-gen retail.',
                'Bhubaneswar, Odisha',
                '₹7–11 LPA',
                'Full-Time',
                'Onsite',
                6.0,
                2026,
                ['Python', 'Java', 'SQL', 'REST API', 'Cloud'],
                deadline_90,
            ),
            (
                'AI & Data Engineering Intern',
                'TCS Digital',
                'Assist in building automated ETL pipelines, predictive machine learning models, and executive analytics dashboards.',
                'Bhubaneswar, Odisha',
                '₹25,000 / month',
                'Internship',
                'Onsite',
                6.0,
                2026,
                ['Python', 'SQL', 'Pandas', 'NumPy', 'Machine Learning'],
                deadline_45,
            ),

            # Tech Innovations Inc.
            (
                'Python Backend Developer',
                'Tech Innovations Inc.',
                'Build resilient Python microservices and REST APIs for a growing enterprise product team.',
                'Bhubaneswar, Odisha',
                '₹6–10 LPA',
                'Full-Time',
                'Hybrid',
                6.5,
                2026,
                ['Python', 'Django', 'REST API', 'SQL'],
                deadline_45,
            ),
            (
                'Generative AI Fullstack Developer',
                'Tech Innovations Inc.',
                'Build end-to-end intelligent copilot interfaces with modern LLM orchestration and vector database retrieval.',
                'Pune, Maharashtra',
                '₹12–20 LPA',
                'Full-Time',
                'Hybrid',
                7.0,
                2026,
                ['Python', 'Django', 'React', 'LLM', 'RAG', 'APIs'],
                deadline_60,
            ),
        ]

        for item in job_catalog:
            title, comp_name, desc, loc, sal, jtype, wmode, cgpa, grad_yr, req_skills, dline = item
            company_obj = companies[comp_name]
            existing_jobs = list(Job.objects.filter(title=title, company=company_obj))
            if existing_jobs:
                job_obj = existing_jobs[0]
                for extra in existing_jobs[1:]:
                    extra.delete()
                job_obj.description = desc
                job_obj.location = loc
                job_obj.salary = sal
                job_obj.job_type = jtype
                job_obj.work_mode = wmode
                job_obj.minimum_cgpa = cgpa
                job_obj.graduation_year = grad_yr
                job_obj.application_deadline = dline
                job_obj.is_verified = True
                job_obj.save()
            else:
                job_obj = Job.objects.create(
                    title=title,
                    company=company_obj,
                    description=desc,
                    location=loc,
                    salary=sal,
                    job_type=jtype,
                    work_mode=wmode,
                    minimum_cgpa=cgpa,
                    graduation_year=grad_yr,
                    application_deadline=dline,
                    is_verified=True,
                )
            job_skills = [skills[sn] for sn in req_skills if sn in skills]
            job_obj.required_skills.set(job_skills)

        # Update company open position counters
        for comp_name, comp_obj in companies.items():
            comp_obj.open_positions = comp_obj.jobs.filter(job_type='Full-Time').count()
            comp_obj.internship_opportunities = comp_obj.jobs.filter(job_type='Internship').count()
            comp_obj.save(update_fields=['open_positions', 'internship_opportunities'])

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {len(companies)} top startups/companies and {len(job_catalog)} career opportunities!'))
