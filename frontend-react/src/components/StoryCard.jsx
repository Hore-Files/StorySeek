import { useState } from 'react';
import { ChevronDown, ChevronUp, Sparkles, AlertCircle } from 'lucide-react';

export default function StoryCard({ hit, onMoreLikeThis }) {
  const [showExplanation, setShowExplanation] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [isExpHovered, setIsExpHovered] = useState(false);
  const { work, score, explanation } = hit;
  const warnings = (work.content_warnings || []).filter(w => w !== 'none');
  const sourceLabel = work.source === 'project_gutenberg'
    ? 'Project Gutenberg'
    : work.source || 'Unknown source';

  const pillStyle = (bg, color) => ({
    padding: '5px 14px',
    backgroundColor: bg,
    color,
    borderRadius: 9999,
    fontSize: 11,
    fontWeight: 600,
    letterSpacing: '0.05em',
    textTransform: 'uppercase',
    display: 'inline-block',
  });

  const tagStyle = (bg, color) => ({
    padding: '4px 12px',
    backgroundColor: bg,
    color,
    borderRadius: 9999,
    fontSize: 12,
    fontWeight: 500,
  });

  const topMeta = [work.format, work.status, work.length_bucket, work.audience_rating].filter(Boolean);

  return (
    <article className="ss-card" style={{
      backgroundColor: '#fff',
      border: '1px solid rgba(237, 242, 247, 0.7)',
      borderRadius: 20,
      padding: '28px 32px',
      boxShadow: '0 20px 40px -10px rgba(0,0,0,0.05)',
      display: 'flex',
      flexDirection: 'column',
      gap: 16,
      transition: 'background-color 0.3s ease',
    }}>
      {/* ── Header: Title + Meta Tags ── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16 }}>
        <div style={{ minWidth: 0 }}>
          <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: 20, fontWeight: 700, color: 'var(--color-on-surface)', marginBottom: 4 }}>
            {work.title}
          </h3>
          <p style={{ fontSize: 13, color: 'var(--color-on-surface-variant)', marginBottom: 8 }}>
            by {work.creator}
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: score !== undefined ? 8 : 0 }}>
            <span className="ss-pill" style={pillStyle('rgba(219,234,254,0.7)', '#1e40af')}>
              {sourceLabel}
            </span>
            <span className="ss-pill" style={pillStyle('rgba(193,198,215,0.3)', '#414754')}>
              ID {work.work_id}
            </span>
          </div>
          {score !== undefined && (
            <p style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>Relevance score: {score.toFixed(2)}</p>
          )}
        </div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', justifyContent: 'flex-end', flexShrink: 0 }}>
          {topMeta.slice(0, 2).map((m, i) => (
            <span key={i} className="ss-pill" style={pillStyle('#eeeeee', '#718096')}>{m}</span>
          ))}
        </div>
      </div>

      {/* ── Summary ── */}
      <p style={{
        color: 'var(--color-on-surface-variant)', lineHeight: 1.65,
        fontSize: 15, display: '-webkit-box', WebkitLineClamp: 3,
        WebkitBoxOrient: 'vertical', overflow: 'hidden',
      }}>
        {work.summary}
      </p>

      {/* ── Tags: Tropes & Themes ── */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {work.tropes?.length > 0 && (
          <div>
            <p style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#c1c9be', marginBottom: 6 }}>Tropes</p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {work.tropes.map((t, i) => (
                <span key={i} className="ss-tag-trope" style={tagStyle('rgba(165,214,167,0.15)', '#325e39')}>{t}</span>
              ))}
            </div>
          </div>
        )}
        {work.themes?.length > 0 && (
          <div>
            <p style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#c1c9be', marginBottom: 6 }}>Themes</p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {work.themes.map((t, i) => (
                <span key={i} className="ss-tag-theme" style={tagStyle('rgba(219,234,254,0.7)', '#1e40af')}>{t}</span>
              ))}
            </div>
          </div>
        )}
        {work.genres?.length > 0 && (
          <div>
            <p style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#c1c9be', marginBottom: 6 }}>Genres</p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {work.genres.map((g, i) => (
                <span key={i} className="ss-tag-genre" style={tagStyle('rgba(193,198,215,0.3)', '#414754')}>{g}</span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ── Content Warnings ── */}
      {warnings.length > 0 && (
        <div className="ss-warning" style={{
          padding: '10px 14px', borderRadius: 10, display: 'flex', alignItems: 'center', gap: 8, fontSize: 13,
          backgroundColor: '#fffbeb', color: '#b45309',
          border: '1px solid #fde68a',
        }}>
          <AlertCircle size={14} style={{ flexShrink: 0, color: '#d97706' }} />
          <span><strong>Content warnings:</strong> {warnings.join(', ')}</span>
        </div>
      )}

      {/* ── Footer: Why matched + CTA ── */}
      <div style={{ borderTop: '1px solid var(--color-border-light)', paddingTop: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
        {/* Why this matched accordion */}
        {explanation?.length > 0 && (
          <div>
            <button
              onClick={() => setShowExplanation(!showExplanation)}
              onMouseEnter={() => setIsExpHovered(true)}
              onMouseLeave={() => setIsExpHovered(false)}
              style={{
                display: 'flex', alignItems: 'center', gap: 6, background: 'none',
                backgroundColor: isExpHovered ? 'rgba(0, 0, 0, 0.02)' : 'transparent',
                padding: '6px 12px',
                marginLeft: -12,
                width: 'calc(100% + 24px)',
                borderRadius: 8,
                border: 'none', cursor: 'pointer', fontFamily: 'inherit',
                fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em',
                color: isExpHovered ? 'var(--color-on-surface)' : 'var(--color-text-secondary)',
                transition: 'all 0.2s ease',
              }}
            >
              <Sparkles size={14} color={isExpHovered ? 'var(--color-primary)' : '#A5D6A7'} style={{ transition: 'color 0.2s ease' }} />
              Why this matched
              <span style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center' }}>
                {showExplanation ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </span>
            </button>
            {showExplanation && (
              <div style={{ paddingTop: 10, fontSize: 13, color: 'var(--color-on-surface-variant)', lineHeight: 1.7 }}>
                {explanation.map((b, i) => <p key={i}>• {b}</p>)}
              </div>
            )}
          </div>
        )}

        {/* More Like This button */}
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button
            onClick={() => onMoreLikeThis(work)}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            className="ss-btn-primary"
            style={{
              backgroundColor: isHovered ? '#8fc292' : '#A5D6A7', color: '#fff',
              border: 'none', padding: '9px 22px', borderRadius: 9999,
              fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em',
              cursor: 'pointer', fontFamily: 'inherit',
              boxShadow: '0 4px 12px rgba(165,214,167,0.35)',
              transition: 'background-color 0.2s, opacity 0.2s',
            }}
          >
            More Like This
          </button>
        </div>
      </div>
    </article>
  );
}
