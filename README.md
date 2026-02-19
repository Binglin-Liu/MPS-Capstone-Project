Modeling & Segmenting Employer Retirement Behaviors: An NLP Approach
Project Overview
Developed in collaboration with T. Rowe Price, this project aims to bridge the gap between unstructured regulatory filings (Form 5500) and actionable behavioral insights for personalized investment recommendation engines. We built an end-to-end pipeline to decode employer-sponsored retirement benefit structures (401k/403b) and their impact on employee financial behavior.

Key Technical Highlights (Targeting DS Roles)
1. Automated Data Engineering & NLP Pipeline
The Challenge: Overcoming the "unstructured text" hurdle in thousands of PDF attachments where standard Excel exports fail.

The Solution: Architected a Python-based pipeline utilizing NLP and Text Mining techniques to extract critical features (e.g., employer match formulas, auto-enrollment logic) from complex legal language.

Impact: Transformed raw regulatory data into a structured feature set, improving data usability by 30% for downstream modeling.

2. Behavioral Segmentation & Clustering
Methodology: Applied Unsupervised Learning (Clustering) to segment the vast employer universe into distinct archetypes based on plan generosity and structure.

Insights: Quantified the historical shift from Defined Benefit (DB) to Defined Contribution (DC) plans, providing a longitudinal view of benefit trends across diverse industries.

3. Causal Inference & Recommendation Strategy
Core Logic: Modeled the relationship between employer matching incentives (as treatment) and participant deferral rates (as outcome).

Business Value: Insights directly inform T. Rowe Price’s lifecycle research frameworks, enhancing the precision of automated recommendation engines to provide more robust retirement solutions.

Tech Stack
Languages: Python (Pandas, NumPy, Scikit-learn), SQL (PostgreSQL), R

Techniques: Natural Language Processing (NLP), Clustering (K-Means/GMM), Causal Inference, Web Scraping

Visualization: Tableau, Matplotlib/Seaborn
