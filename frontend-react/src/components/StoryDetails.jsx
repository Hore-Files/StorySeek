import {
  AlertCircle,
  ArrowLeft,
  BookOpen,
  Calendar,
  Database,
  ExternalLink,
  FileText,
  Languages,
  Sparkles,
  Tag,
  User,
} from 'lucide-react';

const formatValue = (value) => {
  if (!value) return 'Unknown';
  return String(value).replaceAll('_', ' ');
};

const cleanList = (items = []) => items.filter(Boolean).filter(item => item !== 'none' && item !== 'unknown');

function DetailPill({ children, variant = 'default' }) {
  return (
    <span className={`ss-detail-pill ss-detail-pill-${variant}`}>
      {children}
    </span>
  );
}

function DetailSection({ title, icon: Icon, children }) {
  return (
    <section className="ss-detail-section">
      <div className="ss-detail-section-title">
        <Icon size={16} />
        <span>{title}</span>
      </div>
      {children}
    </section>
  );
}

function MetadataItem({ label, value, icon: Icon }) {
  return (
    <div className="ss-detail-meta-item">
      <Icon size={16} />
      <div>
        <span>{label}</span>
        <strong>{formatValue(value)}</strong>
      </div>
    </div>
  );
}

function TagGroup({ title, items, variant }) {
  const values = cleanList(items);
  if (!values.length) return null;

  return (
    <div>
      <p className="ss-detail-kicker">{title}</p>
      <div className="ss-detail-tag-row">
        {values.map((item, index) => (
          <DetailPill key={`${item}-${index}`} variant={variant}>{item}</DetailPill>
        ))}
      </div>
    </div>
  );
}

const getGutenbergBookId = (work) => {
  const normalizeId = (value) => {
    const parsed = Number.parseInt(String(value || ''), 10);
    return Number.isFinite(parsed) ? String(parsed) : null;
  };

  if (work?.book_id) return normalizeId(work.book_id);
  const match = String(work?.work_id || '').match(/(?:pg|g)_(\d+)/i);
  return match ? normalizeId(match[1]) : null;
};

export default function StoryDetails({ hit, work, onBack, onMoreLikeThis }) {
  const activeWork = work || hit?.work;
  if (!activeWork) return null;

  const warnings = cleanList(activeWork.content_warnings);
  const explanation = hit?.explanation || [];
  const matchedPassages = hit?.matched_passages || [];
  const score = hit?.score;
  const gutenbergBookId = activeWork.source === 'project_gutenberg' ? getGutenbergBookId(activeWork) : null;
  const gutenbergUrl = gutenbergBookId
    ? `https://www.gutenberg.org/ebooks/${gutenbergBookId}`
    : null;

  return (
    <div className="ss-detail-page">
      <button className="ss-detail-back" onClick={onBack}>
        <ArrowLeft size={16} />
        Back to results
      </button>

      <section className="ss-detail-hero">
        <div className="ss-detail-cover" aria-hidden="true">
          <BookOpen size={42} />
        </div>

        <div className="ss-detail-hero-copy">
          <div className="ss-detail-eyebrow">
            <span>{formatValue(activeWork.format)}</span>
            <span>{formatValue(activeWork.status)}</span>
            <span>{formatValue(activeWork.length_bucket)}</span>
          </div>
          <h1>{activeWork.title}</h1>
          <p className="ss-detail-author">by {formatValue(activeWork.creator)}</p>
          <div className="ss-detail-actions">
            <button className="ss-btn-primary ss-detail-primary-action" onClick={() => onMoreLikeThis(activeWork)}>
              <Sparkles size={15} />
              More Like This
            </button>
            {gutenbergUrl && (
              <a className="ss-detail-source-link" href={gutenbergUrl} target="_blank" rel="noreferrer">
                <ExternalLink size={15} />
                Open Source
              </a>
            )}
          </div>
        </div>
      </section>

      <div className="ss-detail-layout">
        <div className="ss-detail-main">
          <DetailSection title="Summary" icon={FileText}>
            <p className="ss-detail-summary">{activeWork.summary || 'No summary available.'}</p>
          </DetailSection>

          {explanation.length > 0 && (
            <DetailSection title="Why This Matched" icon={Sparkles}>
              <div className="ss-detail-explanation">
                {explanation.map((item, index) => (
                  <p key={`${item}-${index}`}>{item}</p>
                ))}
              </div>
            </DetailSection>
          )}

          {matchedPassages.length > 0 && (
            <DetailSection title="Matched Passages" icon={FileText}>
              <div className="ss-detail-passage-list">
                {matchedPassages.map((passage) => (
                  <article key={passage.chunk_id} className="ss-detail-passage">
                    <span>Chunk {passage.chunk_index} | score {Number(passage.score).toFixed(2)}</span>
                    <p>{passage.text_chunk}</p>
                  </article>
                ))}
              </div>
            </DetailSection>
          )}

          <DetailSection title="Story Signals" icon={Tag}>
            <div className="ss-detail-tag-stack">
              <TagGroup title={activeWork.source === 'project_gutenberg' ? 'Topics' : 'Genres'} items={activeWork.genres} variant="genre" />
              <TagGroup title={activeWork.source === 'project_gutenberg' ? 'Subjects' : 'Themes'} items={activeWork.themes} variant="theme" />
              <TagGroup title="Tropes" items={activeWork.tropes} variant="trope" />
              <TagGroup title="Relationship Dynamics" items={activeWork.relationship_dynamics} variant="default" />
              <TagGroup title="Topics" items={activeWork.topics} variant="default" />
              <TagGroup title="Project Gutenberg Subjects" items={activeWork.pg_subjects} variant="subject" />
            </div>
          </DetailSection>
        </div>

        <aside className="ss-detail-side">
          <DetailSection title="Details" icon={Database}>
            <div className="ss-detail-meta-grid">
              <MetadataItem label="Audience" value={activeWork.audience_rating} icon={User} />
              <MetadataItem label="Language" value={activeWork.language} icon={Languages} />
              <MetadataItem label="Source" value={activeWork.source} icon={Database} />
              <MetadataItem label="Release Date" value={activeWork.release_date} icon={Calendar} />
              <MetadataItem label="Work ID" value={activeWork.work_id} icon={FileText} />
              {gutenbergBookId && <MetadataItem label="Book ID" value={gutenbergBookId} icon={BookOpen} />}
              {score !== undefined && <MetadataItem label="Relevance" value={score.toFixed(2)} icon={Sparkles} />}
            </div>
          </DetailSection>

          {warnings.length > 0 && (
            <DetailSection title="Content Warnings" icon={AlertCircle}>
              <div className="ss-detail-warning-list">
                {warnings.map((warning, index) => (
                  <span key={`${warning}-${index}`}>{warning}</span>
                ))}
              </div>
            </DetailSection>
          )}
        </aside>
      </div>
    </div>
  );
}
