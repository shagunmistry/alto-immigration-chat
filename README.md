# Alto - An AI-powered Immigration Assistant

A Streamlit-based web application that provides accurate immigration information through AI-powered search of official government websites.

## Features

- **AI-Powered Responses**: Utilizes OpenAI's GPT-4o and embedding models to provide accurate, context-aware responses
- **Official Source Data**: Scrapes and indexes information from official government immigration websites
- **Multi-Country Support**: Currently supports US and Canadian immigration resources
- **Automatic Updates**: Configurable scraping interval to keep information current
- **Vector Search**: Uses embeddings and semantic search to find the most relevant information
- **Chat Interface**: User-friendly chat UI built with Streamlit
- **Data Persistence**: Stores scraped content and embeddings in Supabase

## Installation

### Prerequisites

- Python 3.12.9 or higher
- Streamlit
- OpenAI API key
- Supabase account and credentials

### Setup

1. Clone the repository:

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your credentials:
```
OPENAI_API_KEY=your_openai_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SCRAPE_INTERVAL_DAYS=7
```

4. Run the application:
```bash
streamlit run app.py
```

## Database Setup

The application requires the following tables in your Supabase database:

1. `immigration_website_chunks` - Stores the website content chunks and embeddings
2. `immigration_website_scrape_status` - Tracks when websites were last scraped

Schema definitions are available in the `database_setup.sql` file.

## Usage

1. Select the country and specific immigration websites from the sidebar
2. Click "Check & Update Website Data" to ensure you have the latest information
3. Ask your immigration-related questions in the chat interface

## Customizing Sources

To add or modify the immigration information sources, edit the `constants.py` file:

```python
us_websites = {
    "USCIS General": ["https://www.uscis.gov/..."],
    "Work Visas": ["https://www.uscis.gov/working-in-the-united-states", ...],
    # Add more categories and URLs
}

canada_websites = {
    "Immigration Canada": ["https://www.canada.ca/en/immigration-refugees-citizenship..."],
    # Add more categories and URLs
}
```

## Architecture

The application follows these main processes:

1. **Data Collection**:
   - Scrapes content from official immigration websites
   - Breaks content into manageable chunks
   - Computes vector embeddings for each chunk
   - Stores chunks and embeddings in Supabase

2. **Query Processing**:
   - Receives user questions via chat interface
   - Converts question to vector embedding
   - Retrieves most relevant content chunks using similarity search
   - Sends context and question to GPT-4o for processing
   - Returns answer with citation sources

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Disclaimer

This tool is meant to provide general information about immigration procedures and is not a substitute for legal advice. Always consult with an immigration lawyer or official government resources for your specific case.

## Local Development

- Run locally with the following command:

```bash
streamlit run app.py
```

### Test questions

- How long can I get my pgwp after studying in Canada?
- Can my common law spouse be included in my express entry application?
- What programs are eligible for the pgwp?
- How long can I work in Canada with a pgwp?

#### American Test questions

Here are some test questions you can use to evaluate your Immigration Consultant Assistant with Supabase integration:

##### Basic Functionality Questions

1. "What are the eligibility requirements for a green card in the United States?"
2. "How long does the naturalization process typically take?"
3. "What's the difference between adjustment of status and consular processing?"
4. "Can you explain the child status protection act?"
5. "What documents are needed for the green card interview?"

##### Questions to Test Content Retrieval

6. "What visa options do I have if I want to work temporarily in the US?"
7. "How can I apply for citizenship if I'm married to a US citizen?"
8. "What are the current processing times for employment-based green cards?"
9. "Explain the public charge rule and how it affects green card applications."
10. "What happens if my green card application is denied?"

##### Edge Case Questions

11. "I've been a permanent resident for 4 years. Can I apply for citizenship?"
12. "How does having a criminal record affect my immigration status?"
13. "What happens to my immigration status if I get divorced during the green card process?"
14. "Can I travel outside the US while my adjustment of status application is pending?"
15. "How do I renew my employment authorization document?"

##### Questions That Test Multiple Categories

16. "I'm on an H-1B visa. What's the process to get a green card and eventually citizenship?"
17. "What immigration benefits are available to immediate relatives of US citizens?"
18. "How do priority dates work for family-based immigration, and how can I check my status?"
19. "What are my options if my visa has expired but I'm still in the US?"
20. "How do I prepare for the naturalization test and interview?"

#### Canadian Test questions

##### Federal Programs

1. What are the main eligibility criteria for Express Entry?
2. How does the Comprehensive Ranking System (CRS) work for Express Entry applications?
3. What is the difference between the Federal Skilled Worker Program and the Federal Skilled Trades Program?
4. What family members can I sponsor to immigrate to Canada?
5. What are the income requirements for family sponsorship?
6. How long does the Express Entry application process typically take?
7. What is an Invitation to Apply (ITA) in the Express Entry system?
8. What documents are required for a complete Express Entry profile?

##### Provincial Nominee Programs

1. What are the differences between the Ontario Immigrant Nominee Program streams?
2. How does the BC PNP Tech program work?
3. What are the requirements for Alberta's Rural Immigration Stream?
4. What are the unique features of Quebec's immigration system compared to other provinces?
5. Which Manitoba PNP streams are available for entrepreneurs?
6. What are the advantages of applying through Saskatchewan's Express Entry category?
7. How does Nova Scotia's Labour Market Priorities Stream identify candidates?
8. What is the New Brunswick Strategic Initiative stream designed for?
9. What business immigration options are available through Prince Edward Island?
10. What are the requirements for healthcare professionals under Newfoundland and Labrador's PNP?
11. How does the Yukon Community Program differ from other territorial nominee programs?
12. What industries are prioritized in the Northwest Territories nominee program?
13. What are the settlement fund requirements for Nunavut's nominee program?

##### Study Permits

1. How long can I stay in Canada with a study permit?
2. What are the requirements for a Post-Graduation Work Permit (PGWP)?
3. Can I work while studying in Canada?
4. What is the Student Direct Stream and which countries are eligible?
5. How can I extend my study permit if my program takes longer than expected?

##### Work Permits

1. What is the difference between LMIA-based work permits and LMIA-exempt work permits?
2. How does the Global Talent Stream work?
3. What are the requirements for an Open Work Permit?
4. How can I transition from a temporary work permit to permanent residence?
5. What is the maximum duration of a TFWP (Temporary Foreign Worker Program) work permit?

##### Citizenship

1. What are the residency requirements for Canadian citizenship?
2. How do I prepare for the Canadian citizenship test?
3. What language proficiency level is required for citizenship?
4. Can I hold dual citizenship when becoming a Canadian citizen?
5. How long does the citizenship application process take?

##### Cross-Category Questions

1. How do immigration programs differ for skilled workers versus entrepreneurs?
2. What are the differences in processing times between Express Entry and Provincial Nominee Programs?
3. How has COVID-19 affected Canadian immigration policies and processing?
4. What is a Police Clearance Certificate and when is it required?
5. What are the differences in healthcare coverage for permanent residents versus temporary residents?
6. How do I prove my language proficiency for different immigration programs?
7. What are the main differences between applying for immigration to Quebec versus other provinces?
8. How do the Atlantic Immigration Program and Provincial Nominee Programs compare?
9. What are my options if my immigration application is refused?
10. How do education credential assessments work for foreign degrees?
---