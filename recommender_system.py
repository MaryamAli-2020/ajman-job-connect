from sentence_transformers import SentenceTransformer, util
import pandas as pd

class JobRecommender:
    def __init__(self, jobs_df):
        self.model = SentenceTransformer('bert-base-nli-mean-tokens')
        self.jobs_df = jobs_df
        self._prepare_data()

    def _prepare_data(self):
        self.jobs_df['description'] = self.jobs_df['description'].fillna('')
        self.job_embeddings = self.model.encode(self.jobs_df['description'].tolist(), convert_to_tensor=True)

    def recommend_jobs(self, job_title, top_n=5):
        query_embedding = self.model.encode(job_title, convert_to_tensor=True)
        cosine_scores = util.cos_sim(query_embedding, self.job_embeddings)[0]

        # Ensure top_n is within the range of available cosine_scores
        if top_n > len(cosine_scores):
            top_n = len(cosine_scores)

        top_results = cosine_scores.topk(k=top_n)

        recommendations = []
        for score, idx in zip(top_results[0], top_results[1]):
            idx = int(idx)  # Convert idx to integer to ensure it's a valid index
            if idx < len(self.jobs_df) and idx >= 0:  # Check if idx is within DataFrame index range
                recommendations.append({
                    "title": self.jobs_df.iloc[idx]['title'],
                    "company": self.jobs_df.iloc[idx]['company'],
                    "location": self.jobs_df.iloc[idx]['location'],
                    "link": self.jobs_df.iloc[idx]['link'],
                    "description": self.jobs_df.iloc[idx]['description'],
                    "score": score.item()
                })
        
        return recommendations
