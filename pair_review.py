"""Build reviewable cross-document pairs; never award semantic credit automatically."""
def build_pair_review(report, model=None, minimum=0.65):
    resume = list(report.resume_mentions)
    job = list(report.job_mentions)
    requirements = {}
    for mention in job:
        uri = mention.skill.uri
        row = requirements.setdefault(uri, {'uri': uri, 'skill': mention.skill.preferred_label,
            'texts': [], 'confirmed': False, 'matched': False, 'candidates': []})
        if mention.matched_text not in row['texts']:
            row['texts'].append(mention.matched_text)
        row['confirmed'] |= mention.is_confirmed
    confirmed_resume = {m.skill.uri for m in resume if m.is_confirmed}
    for row in requirements.values():
        row['matched'] = row['confirmed'] and row['uri'] in confirmed_resume
    scores = None
    if model is not None and resume and job:
        import numpy as np
        vectors = np.asarray(model.encode([m.matched_text for m in job + resume],
            convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False), dtype=float)
        if vectors.ndim != 2 or len(vectors) != len(job) + len(resume) or not np.isfinite(vectors).all():
            raise ValueError('Invalid review embeddings')
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        vectors = vectors / np.maximum(norms, 1e-12)
        scores = vectors[:len(job)] @ vectors[len(job):].T
    for row in requirements.values():
        if row['matched']:
            continue
        candidates = {}
        for j, requirement in enumerate(job):
            if requirement.skill.uri != row['uri']:
                continue
            for r, evidence in enumerate(resume):
                same = evidence.skill.uri == row['uri']
                score = float(scores[j, r]) if scores is not None else None
                if not same and (score is None or score < minimum):
                    continue
                key = (evidence.skill.uri, evidence.matched_text)
                candidate = {'resume_uri': evidence.skill.uri, 'resume_skill': evidence.skill.preferred_label,
                    'resume_text': evidence.matched_text, 'job_text': requirement.matched_text,
                    'similarity': round(score, 3) if score is not None else None,
                    'same_catalog_skill': same}
                old = candidates.get(key)
                if old is None or (score or 0) > (old['similarity'] or 0):
                    candidates[key] = candidate
        row['candidates'] = sorted(candidates.values(),
            key=lambda c: (c['same_catalog_skill'], c['similarity'] or 0), reverse=True)[:3]
    return list(requirements.values())
