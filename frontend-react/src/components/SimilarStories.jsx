import React, { useState, useEffect } from 'react';
import StoryCard from './StoryCard';
import { Loader2, ArrowLeft, BookOpen } from 'lucide-react';

// Compact anchor card — shows the selected work as a reference
function AnchorCard({ work }) {
  const tags = [...(work.tropes || []), ...(work.themes || [])].slice(0, 4);
  return (
    <div className="ss-anchor-card" style={{
      backgroundColor: '#ffffff',
      border: '1px solid var(--color-border-light)',
      borderLeft: '6px solid var(--color-primary)',
      borderRadius: 20,
      padding: '20px 28px',
      display: 'flex',
      gap: 20,
      alignItems: 'flex-start',
      boxShadow: '0 10px 30px -10px rgba(0,0,0,0.04)',
      transition: 'background-color 0.3s ease',
    }}>
      {/* Icon */}
      <div style={{
        width: 48, height: 48, borderRadius: 14, flexShrink: 0,
        backgroundColor: 'rgba(60,104,66,0.1)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <BookOpen size={22} color="var(--color-primary)" />
      </div>

      {/* Info */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <span style={{
          fontSize: 10, fontWeight: 800, textTransform: 'uppercase',
          letterSpacing: '0.12em', color: '#A5D6A7', display: 'block', marginBottom: 4,
        }}>
          Selected Story
        </span>
        <h3 style={{
          fontFamily: 'var(--font-heading)', fontWeight: 700, fontSize: 18,
          color: 'var(--color-on-surface)', marginBottom: 6,
          whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
        }}>
          {work.title}
        </h3>
        <p style={{
          fontSize: 13, color: 'var(--color-on-surface-variant)', lineHeight: 1.55,
          display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden',
        }}>
          {work.summary}
        </p>
        {tags.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 10 }}>
            {tags.map((t, i) => (
              <span key={i} className="ss-tag-trope" style={{
                padding: '3px 10px', borderRadius: 9999, fontSize: 11, fontWeight: 500,
                backgroundColor: 'rgba(165,214,167,0.15)', color: '#325e39',
              }}>
                {t}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function SimilarStories({ work, onClose, backendUrl, onMoreLikeThis }) {
  const [similarHits, setSimilarHits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchSimilar() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${backendUrl}/similar/${work.work_id}?size=8`);
        if (!res.ok) throw new Error('Failed to fetch');
        const data = await res.json();
        setSimilarHits(data.hits || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchSimilar();
  }, [work.work_id, backendUrl]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>

      {/* ── Back button (escape hatch) ── */}
      <button
        onClick={onClose}
        style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          background: 'none', border: 'none', cursor: 'pointer',
          fontFamily: 'inherit', fontSize: 13, fontWeight: 700,
          color: 'var(--color-text-secondary)',
          textTransform: 'uppercase', letterSpacing: '0.08em',
          padding: 0, alignSelf: 'flex-start',
          transition: 'color 0.2s',
        }}
        onMouseEnter={e => e.currentTarget.style.color = 'var(--color-on-surface)'}
        onMouseLeave={e => e.currentTarget.style.color = 'var(--color-text-secondary)'}
      >
        <ArrowLeft size={16} />
        Back to search results
      </button>

      {/* ── Anchor card: the selected story ── */}
      <AnchorCard work={work} />

      {/* ── Section header ── */}
      <div style={{ borderBottom: '1px solid var(--color-border-light)', paddingBottom: 16 }}>
        <span style={{
          fontSize: 11, fontWeight: 700, textTransform: 'uppercase',
          letterSpacing: '0.1em', color: '#A5D6A7', display: 'block', marginBottom: 4,
        }}>
          Similar Stories
        </span>
        <h2 style={{
          fontFamily: 'var(--font-heading)', fontWeight: 700, fontSize: 24,
          color: 'var(--color-on-surface)', margin: 0,
        }}>
          More like <em style={{ fontStyle: 'normal', color: 'var(--color-primary)' }}>"{work.title}"</em>
        </h2>
      </div>

      {/* ── Loading state ── */}
      {loading && (
        <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--color-text-secondary)' }}>
          <Loader2 size={36} style={{ animation: 'spin 1s linear infinite', margin: '0 auto 12px', display: 'block', color: 'var(--color-primary)' }} />
          <p style={{ fontWeight: 500 }}>Finding similar stories...</p>
        </div>
      )}

      {/* ── Error state ── */}
      {error && (
        <div style={{ backgroundColor: '#fef2f2', color: '#991b1b', padding: 16, borderRadius: 12, textAlign: 'center' }}>
          {error}
        </div>
      )}

      {/* ── Empty state ── */}
      {!loading && !error && similarHits.length === 0 && (
        <p style={{ textAlign: 'center', color: 'var(--color-text-secondary)', padding: '40px 0' }}>
          No similar stories found.
        </p>
      )}

      {/* ── Results ── */}
      {!loading && !error && similarHits.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {similarHits.map((hit, i) => (
            <StoryCard
              key={i}
              hit={hit}
              onMoreLikeThis={onMoreLikeThis}
            />
          ))}
        </div>
      )}
    </div>
  );
}
