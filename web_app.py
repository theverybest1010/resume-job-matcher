"""Local Flask interface. Run: python web_app.py (port 5000)."""
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock
import os

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import RequestEntityTooLarge

ROOT = Path(__file__).resolve().parent


def build_pipeline():
    from resume_matcher.skill_catalog import load_skill_catalog
    from resume_matcher.skill_extractor import ExactSkillExtractor
    from resume_matcher.candidate_phrases import CandidatePhraseExtractor
    from resume_matcher.semantic_matcher import SemanticSkillMatcher
    from resume_matcher.hybrid_extractor import HybridSkillExtractor
    from resume_matcher.matching_pipeline import MatchingPipeline

    path = Path(os.environ.get('ESCO_PATH', ROOT / 'data/raw/esco/skills_en.csv'))
    skills = load_skill_catalog(path)
    semantic = SemanticSkillMatcher(skills)
    pipeline = MatchingPipeline(HybridSkillExtractor(
        exact_extractor=ExactSkillExtractor(skills),
        candidate_extractor=CandidatePhraseExtractor(),
        semantic_matcher=semantic,
        min_semantic_score=0.75,
    ))
    pipeline.review_model = semantic.model
    return pipeline


def serialize_report(report, model=None):
    def evidence(mention):
        return {'uri': mention.skill.uri, 'skill': mention.skill.preferred_label, 'text': mention.matched_text,
                'source': mention.source}
    gap = report.skill_gap
    required = len(gap.matched_skills) + len(gap.missing_skills)
    data = {
        'coverage': round(gap.match_percentage, 1) if required else None,
        'matched_count': len(gap.matched_skills), 'required_count': required,
        'text_similarity': round(report.tfidf_similarity * 100, 1),
        'matched': [s.preferred_label for s in gap.matched_skills],
        'missing': [s.preferred_label for s in gap.missing_skills],
        'additional': [s.preferred_label for s in gap.additional_skills],
        'resume_evidence': [evidence(m) for m in report.resume_mentions if m.is_confirmed],
        'job_evidence': [evidence(m) for m in report.job_mentions if m.is_confirmed],
        'resume_suggestions': [evidence(m) for m in report.resume_suggestions],
        'job_suggestions': [evidence(m) for m in report.job_suggestions],
    }
    from pair_review import build_pair_review
    data["requirements"] = build_pair_review(report, model)
    return data


def create_app(pipeline_factory=None):
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 11 * 1024 * 1024
    app.config['MAX_FORM_MEMORY_SIZE'] = 256 * 1024
    app.config['MAX_FORM_PARTS'] = 10
    factory = pipeline_factory or build_pipeline
    pipeline = None
    model_lock = Lock()

    @app.after_request
    def privacy_headers(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
        return response

    @app.errorhandler(RequestEntityTooLarge)
    def too_large(error):
        return jsonify(error='Please use files smaller than 5 MB each.'), 413

    @app.get('/')
    def index():
        return render_template('index.html')

    @app.post('/api/compare')
    def compare():
        nonlocal pipeline
        from resume_matcher.document_loader import extract_document_text

        resume = request.files.get('resume')
        job_url = request.form.get('job_url', '').strip()
        job_text = request.form.get('job_text', '').strip()
        if not resume or not resume.filename:
            return jsonify(error='Add your résumé to continue.'), 400
        if bool(job_url) == bool(job_text):
            return jsonify(error='Paste a job description or enter a job link. Use one option.'), 400
        if len(job_text) > 50000:
            return jsonify(error='Keep the job description under 50,000 characters.'), 400

        def read_upload(upload, folder, name):
            suffix = Path(upload.filename).suffix.lower()
            if suffix != '.pdf':
                raise ValueError('Please upload your résumé as a PDF.')
            content = upload.stream.read(5 * 1024 * 1024 + 1)
            if len(content) > 5 * 1024 * 1024:
                raise ValueError('Please use files smaller than 5 MB each.')
            if not content:
                raise ValueError('One of your files is empty. Please choose another file.')
            path = Path(folder) / (name + suffix)
            path.write_bytes(content)
            try:
                text = extract_document_text(path)
            except Exception:
                raise ValueError(
                    'Could not read your résumé. Please use a readable PDF. '
                    'For scanned or password-protected PDFs, export a text-based copy.'
                ) from None
            if len(text) > 50000:
                raise ValueError('A document is too long. Please keep each under 50,000 characters.')
            return text

        # Temporary files are removed before model initialization or analysis.
        try:
            with TemporaryDirectory(prefix='resume-compare-') as folder:
                resume_text = read_upload(resume, folder, 'resume')
            if job_url:
                from job_links import fetch_job_text
                job_text = fetch_job_text(job_url)
        except ValueError as error:
            return jsonify(error=str(error)), 400

        # Reuse a single model and avoid overlapping CPU inference requests.
        if not model_lock.acquire(blocking=False):
            return jsonify(error='A comparison is already running. Please try again shortly.'), 503
        try:
            if pipeline is None:
                try:
                    pipeline = factory()
                except Exception as error:
                    app.logger.error('Matcher startup failed: %s', type(error).__name__)
                    return jsonify(error='The matcher could not start. Check the server setup and ESCO dataset, then retry.'), 503
            try:
                return jsonify(serialize_report(pipeline.analyze(resume_text, job_text), getattr(pipeline, "review_model", None)))
            except ValueError:
                return jsonify(error='There is not enough usable text to compare. Please check both documents.'), 400
            except Exception:
                return jsonify(error='The comparison could not finish. Please retry or check the server setup.'), 500
        finally:
            model_lock.release()

    return app


if __name__ == '__main__':
    create_app().run(host='0.0.0.0', port=int(os.environ.get('PORT', '5000')), debug=False)
