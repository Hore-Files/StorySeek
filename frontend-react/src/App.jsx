import React, { useState } from 'react';
import { Search, Loader2, X, ChevronDown, ChevronUp, BookOpen, Layers, Theater, Star, AlertTriangle, Users, AlignLeft, Lightbulb, Target, Award, Moon, Sun } from 'lucide-react';
import StoryCard from './components/StoryCard';
import SimilarStories from './components/SimilarStories';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

const FILTER_CATEGORIES = [
  {
    id: 'formats',
    label: 'Format',
    icon: BookOpen,
    options: ["novel", "short_story", "fanfic_style", "manga", "webnovel"],
  },
  {
    id: 'genres',
    label: 'Genre',
    icon: Theater,
    options: ["fantasy", "mystery", "romance", "science fiction", "horror", "historical", "adventure", "drama", "comedy"],
  },
  {
    id: 'tropes',
    label: 'Tropes',
    icon: Layers,
    options: ["slow burn", "enemies to lovers", "rivals to lovers", "found family", "fake dating", "forbidden magic", "time loop", "chosen one", "villain redemption", "academy setting", "kingdom building", "mutual pining", "hurt/comfort"],
  },
  {
    id: 'themes',
    label: 'Themes',
    icon: Lightbulb,
    options: ["dark academia", "political intrigue", "healing", "revenge", "redemption", "grief", "betrayal", "friendship", "identity", "coming of age"],
  },
  {
    id: 'statuses',
    label: 'Status',
    icon: Star,
    options: ["Complete", "Ongoing", "Hiatus"],
  },
  {
    id: 'audiences',
    label: 'Audience',
    icon: Users,
    options: ["General", "Teen", "Mature"],
  },
  {
    id: 'exclude',
    label: 'Exclude Warnings',
    icon: AlertTriangle,
    options: ["major character death", "graphic violence", "abuse", "self harm"],
    danger: true,
  },
];

// ─── Floating Badge ────────────────────────────────────────────────────────────
function FloatingBadge({ Icon, color, style }) {
  return (
    <div className="ss-badge" style={{
      position: 'absolute',
      background: 'rgba(255,255,255,0.92)',
      boxShadow: '0 10px 25px -5px rgba(0,0,0,0.08)',
      borderRadius: 16,
      width: 52,
      height: 52,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color,
      zIndex: 10,
      ...style,
    }}>
      <Icon size={24} strokeWidth={2} />
    </div>
  );
}

// ─── Collapsible Filter Category ───────────────────────────────────────────────
function FilterCategory({ category, selected, onChange }) {
  const [open, setOpen] = useState(false);
  const { id, label, icon: Icon, options, danger } = category;
  const activeCount = selected.length;

  return (
    <div style={{ borderRadius: 12, overflow: 'hidden', border: '1px solid var(--color-border-light)', marginBottom: 8 }}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          width: '100%', display: 'flex', alignItems: 'center', gap: 10,
          padding: '11px 14px', background: open ? 'rgba(60,104,66,0.06)' : '#fff',
          border: 'none', cursor: 'pointer', fontFamily: 'inherit', transition: 'background 0.2s',
        }}
        className={open ? 'ss-filter-open' : 'ss-filter-closed'}
      >
        <Icon size={16} color={danger ? '#b45309' : 'var(--color-primary)'} strokeWidth={2} />
        <span style={{
          flex: 1, textAlign: 'left', fontSize: 11, fontWeight: 700,
          textTransform: 'uppercase', letterSpacing: '0.08em',
          color: danger ? '#92400e' : 'var(--color-on-surface)',
        }}>
          {label}
        </span>
        {activeCount > 0 && (
          <span className="ss-filter-badge-active" style={{
            backgroundColor: 'var(--color-primary)', color: '#fff',
            borderRadius: 9999, width: 18, height: 18, fontSize: 10, fontWeight: 700,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            {activeCount}
          </span>
        )}
        {open ? <ChevronUp size={14} color="var(--color-text-secondary)" /> : <ChevronDown size={14} color="var(--color-text-secondary)" />}
      </button>

      {open && (
        <div className="ss-filter-panel" style={{ padding: '10px 14px 14px', backgroundColor: '#fafafa', borderTop: '1px solid var(--color-border-light)' }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {options.map(opt => {
              const isActive = selected.includes(opt);
              return (
                  <button
                  key={opt}
                  onClick={() => onChange(isActive ? selected.filter(i => i !== opt) : [...selected, opt])}
                  className={isActive ? (danger ? '' : 'ss-chip-active') : 'ss-chip-inactive'}
                  style={{
                    padding: '4px 12px', borderRadius: 9999, fontSize: 12, fontWeight: 500,
                    cursor: 'pointer', transition: 'all 0.15s', fontFamily: 'inherit',
                    backgroundColor: isActive ? (danger ? '#92400e' : 'var(--color-primary)') : '#fff',
                    color: isActive ? '#fff' : 'var(--color-on-surface-variant)',
                    border: `1px solid ${isActive ? (danger ? '#92400e' : 'var(--color-primary)') : 'var(--color-border-light)'}`,
                  }}
                >
                  {opt}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Main App ──────────────────────────────────────────────────────────────────
export default function App() {
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState('bm25');
  const [size, setSize] = useState(10);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({
    formats: [], genres: [], tropes: [], themes: [],
    statuses: [], audiences: [], exclude: [],
  });

  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [similarWork, setSimilarWork] = useState(null);
  const [searchHovered, setSearchHovered] = useState(false);
  const [darkMode, setDarkMode] = useState(false);

  const totalActive = Object.values(filters).flat().length;

  const updateFilter = (key) => (val) => setFilters(prev => ({ ...prev, [key]: val }));
  const clearAll = () => setFilters({ formats: [], genres: [], tropes: [], themes: [], statuses: [], audiences: [], exclude: [] });

  const handleSearch = async (e, targetPage = 1, targetSize = size) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setSimilarWork(null);
    setPage(targetPage);
    setSize(targetSize);

    const payload = {
      query,
      mode,
      page: targetPage,
      size: targetSize,
      exclude_warnings: filters.exclude,
      filters: {
        formats: filters.formats,
        genres: filters.genres,
        tropes: filters.tropes,
        themes: filters.themes,
        statuses: filters.statuses,
        length_buckets: [],
        audience_ratings: filters.audiences,
        languages: [],
      }
    };

    try {
      const res = await fetch(`${BACKEND_URL}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('Backend error: ' + res.statusText);
      setResults(await res.json());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div data-theme={darkMode ? 'dark' : 'light'} style={{ minHeight: '100vh', backgroundColor: 'var(--color-background)', display: 'flex', flexDirection: 'column', fontFamily: 'var(--font-body)', transition: 'background-color 0.3s ease' }}>

      {/* ── Header ── */}
      <header className="ss-header" style={{
        backgroundColor: 'rgba(255,255,255,0.7)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderBottom: '1px solid var(--color-border-light)',
        boxShadow: '0 1px 12px rgba(0,0,0,0.04)',
        position: 'sticky', top: 0, zIndex: 50,
        transition: 'background-color 0.3s ease',
      }}>
        <div style={{ maxWidth: 1440, margin: '0 auto', padding: '16px 32px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 800, fontSize: 22, color: 'var(--color-on-surface)', letterSpacing: '-0.02em' }}>
            StorySeek
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <nav style={{ display: 'flex', gap: 4, background: 'var(--color-surface-dim)', padding: 4, borderRadius: 9999 }}>
              {['bm25', 'dense', 'hybrid'].map(m => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  style={{
                    padding: '6px 20px', borderRadius: 9999, fontSize: 13, fontWeight: 700,
                    textTransform: 'capitalize', cursor: 'pointer', border: 'none', transition: 'all 0.2s',
                    backgroundColor: mode === m ? 'var(--color-on-surface)' : 'transparent',
                    color: mode === m ? (darkMode ? '#0d131f' : '#fff') : 'var(--color-text-secondary)',
                    fontFamily: 'inherit',
                  }}
                >
                  {m}
                </button>
              ))}
            </nav>
            {/* Dark mode toggle */}
            <button
              onClick={() => setDarkMode(!darkMode)}
              style={{
                width: 38, height: 38, borderRadius: 9999,
                backgroundColor: 'var(--color-surface-dim)',
                border: '1px solid var(--color-border-light)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                cursor: 'pointer', transition: 'all 0.2s', color: 'var(--color-on-surface)',
              }}
              title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {darkMode ? <Sun size={16} /> : <Moon size={16} />}
            </button>
          </div>
        </div>
      </header>

      {/* ── Main ── */}
      <main style={{ flex: 1, maxWidth: 1440, margin: '0 auto', width: '100%', padding: '0 10px' }}>

        {/* ── Hero Section ── */}
        <section className="ss-hero-section" style={{
          position: 'relative',
          padding: '60px 48px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 48,
          backgroundColor: '#fff',
          borderRadius: 32,
          border: '1px solid rgba(237, 242, 247, 0.7)',
          boxShadow: '0 20px 40px -15px rgba(0,0,0,0.03)',
          overflow: 'hidden',
          marginBottom: 48,
          marginTop: 24,
          transition: 'background-color 0.3s ease',
        }}>
          {/* Decorative glow (Sage green top-right) */}
          <div style={{
            position: 'absolute', top: 0, right: 0,
            width: 500, height: 500,
            background: 'radial-gradient(circle, rgba(165,214,167,0.15) 0%, transparent 70%)',
            borderRadius: '50%', pointerEvents: 'none',
            transform: 'translate(30%, -20%)',
          }} />

          {/* Decorative glow (Pink bottom-left) */}
          <div style={{
            position: 'absolute', bottom: 0, left: 0,
            width: 500, height: 500,
            background: 'radial-gradient(circle, rgba(255,182,196,0.18) 0%, transparent 70%)',
            borderRadius: '50%', pointerEvents: 'none',
            transform: 'translate(-30%, 30%)',
          }} />

          {/* Left: Text + Search */}
          <div style={{ flex: '0 0 58%', zIndex: 1, position: 'relative' }}>
            <h1 style={{
              fontFamily: 'var(--font-heading)', fontWeight: 800,
              fontSize: 'clamp(32px, 4vw, 52px)', lineHeight: 1.1,
              letterSpacing: '-0.03em', color: 'var(--color-on-surface)',
              marginBottom: 16,
            }}>
              Find the story you're <br />looking for, easier.
            </h1>
            <p style={{ fontSize: 17, color: 'var(--color-text-secondary)', marginBottom: 36, lineHeight: 1.6, maxWidth: 550 }}>
              The most appropriate site to discover stories using natural language — tropes, themes, dynamics and more.
            </p>

            {/* Search bar */}
            <form onSubmit={handleSearch} className="ss-input-search" style={{
              display: 'flex', alignItems: 'center', maxWidth: 640,
              backgroundColor: '#fff',
              border: '1px solid var(--color-border-light)',
              borderRadius: 9999,
              boxShadow: '0 20px 40px -10px rgba(0,0,0,0.08)',
              overflow: 'hidden',
              transition: 'background-color 0.3s ease',
            }}>
              <div style={{ paddingLeft: 20, color: 'var(--color-text-secondary)', display: 'flex', alignItems: 'center' }}>
                <Search size={20} />
              </div>
              <input
                type="text"
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="Find your favorite story here..."
                style={{
                  flex: 1, padding: '16px 12px', fontSize: 15, background: 'transparent',
                  border: 'none', outline: 'none', fontFamily: 'inherit',
                  color: 'var(--color-on-surface)',
                }}
              />
              <div style={{ padding: '6px 6px 6px 0' }}>
                <button
                  type="submit"
                  disabled={loading}
                  onMouseEnter={() => setSearchHovered(true)}
                  onMouseLeave={() => setSearchHovered(false)}
                  className="ss-btn-primary"
                  style={{
                    backgroundColor: searchHovered ? '#8fc292' : '#A5D6A7', color: '#fff',
                    padding: '10px 24px', borderRadius: 9999,
                    fontSize: 14, fontWeight: 700, border: 'none',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    display: 'flex', alignItems: 'center', gap: 6,
                    fontFamily: 'inherit', transition: 'background-color 0.2s, opacity 0.2s',
                    opacity: loading ? 0.7 : 1,
                  }}
                >
                  {loading && <Loader2 size={15} style={{ animation: 'spin 1s linear infinite' }} />}
                  Search
                </button>
              </div>
            </form>
          </div>

          {/* Right: Book image with floating badges */}
          <div style={{ flex: '0 0 38%', position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 340 }}>
            <FloatingBadge Icon={Lightbulb} color="#A5D6A7" style={{ top: '5%', left: '8%', animation: 'float1 4s ease-in-out infinite' }} />
            <FloatingBadge Icon={Target} color="#FFB084" style={{ bottom: '15%', left: '12%', animation: 'float2 3.5s ease-in-out infinite' }} />
            <FloatingBadge Icon={Award} color="#B2B5E5" style={{ top: '25%', right: '2%', animation: 'float3 4.5s ease-in-out infinite' }} />

            <div className="ss-image-card" style={{
              borderRadius: 32,
              overflow: 'hidden',
              width: '100%',
              maxWidth: 480,
              aspectRatio: '4/3',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: 'rgba(255,255,255,0.4)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255,255,255,0.6)',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.06)',
            }}>
              <img
                src="/book-1.png"
                alt="Hand holding a stack of pastel books"
                style={{
                  objectFit: 'contain',
                  width: '95%',
                  height: '95%',
                  transform: 'scale(1.2)',
                  filter: 'drop-shadow(0 15px 25px rgba(0,0,0,0.15))'
                }}
              />
            </div>
          </div>
        </section>

        {/* ── Layout: Sidebar + Results ── */}
        <div style={{ display: 'flex', gap: 48, paddingBottom: 80, alignItems: 'flex-start' }}>

          {/* ── Sidebar Filters ── */}
          <aside style={{ width: 240, flexShrink: 0, position: 'sticky', top: 88 }}>
            <div className="ss-surface" style={{
              backgroundColor: '#fff',
              borderRadius: 20,
              boxShadow: '0 20px 40px -10px rgba(0,0,0,0.06)',
              padding: '20px 16px',
              transition: 'background-color 0.3s ease',
            }}>
              <div style={{ marginBottom: 16 }}>
                <h2 style={{ fontFamily: 'var(--font-heading)', fontWeight: 700, fontSize: 16, color: 'var(--color-on-surface)', marginBottom: 4 }}>
                  Filters
                </h2>
                <p style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>Refine your search results</p>
              </div>

              {FILTER_CATEGORIES.map(cat => (
                <FilterCategory
                  key={cat.id}
                  category={cat}
                  selected={filters[cat.id]}
                  onChange={updateFilter(cat.id)}
                />
              ))}

              {totalActive > 0 && (
                <button
                  onClick={clearAll}
                  style={{
                    width: '100%', padding: '10px', marginTop: 8,
                    backgroundColor: 'transparent', border: 'none',
                    fontSize: 11, fontWeight: 700, textTransform: 'uppercase',
                    letterSpacing: '0.08em', color: 'var(--color-text-secondary)',
                    cursor: 'pointer', fontFamily: 'inherit', transition: 'color 0.2s',
                  }}
                >
                  Clear All Filters ({totalActive})
                </button>
              )}
            </div>
          </aside>

          {/* ── Results Area ── */}
          <section style={{ flex: 1, minWidth: 0 }}>

            {error && (
              <div className="ss-error-box" style={{ backgroundColor: '#fef2f2', color: '#991b1b', padding: '14px 20px', borderRadius: 16, marginBottom: 24, display: 'flex', alignItems: 'center', gap: 10 }}>
                <X size={18} /><span style={{ fontWeight: 500 }}>{error}</span>
              </div>
            )}

            {loading && (
              <div style={{ textAlign: 'center', padding: '80px 0', color: 'var(--color-text-secondary)' }}>
                <Loader2 size={40} style={{ animation: 'spin 1s linear infinite', margin: '0 auto 12px', display: 'block', color: 'var(--color-primary)' }} />
                <p style={{ fontWeight: 500 }}>Searching stories...</p>
              </div>
            )}

            {/* ── "More Like This" Focused View ── */}
            {similarWork && !loading && (
              <SimilarStories
                work={similarWork}
                backendUrl={BACKEND_URL}
                onClose={() => setSimilarWork(null)}
                onMoreLikeThis={setSimilarWork}
              />
            )}

            {/* ── Normal Search Results View ── */}
            {results && !loading && !similarWork && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', borderBottom: '1px solid var(--color-border-light)', paddingBottom: 16, marginBottom: 32 }}>
                  <div>
                    <span style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--color-primary)', display: 'block', marginBottom: 4 }}>
                      Search Results
                    </span>
                    <h2 style={{ fontFamily: 'var(--font-heading)', fontWeight: 700, fontSize: 26, color: 'var(--color-on-surface)', margin: 0 }}>
                      Curated Results
                    </h2>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                    <span style={{ fontSize: 14, color: 'var(--color-text-secondary)' }}>
                      Showing <strong>{((page - 1) * size) + 1} - {Math.min(page * size, results.total)}</strong> of <strong>{results.total}</strong> matches · <strong>{results.mode}</strong>
                    </span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: 'var(--color-text-secondary)' }}>
                      <span>Show:</span>
                      <select
                        className="ss-select"
                        value={size}
                        onChange={(e) => {
                          const newSize = Number(e.target.value);
                          setSize(newSize);
                          handleSearch(null, 1, newSize);
                        }}
                        style={{
                          padding: '4px 8px',
                          borderRadius: 8,
                          border: '1px solid var(--color-border-light)',
                          backgroundColor: '#fff',
                          color: 'var(--color-on-surface)',
                          fontSize: 13,
                          fontWeight: 600,
                          outline: 'none',
                          cursor: 'pointer',
                        }}
                      >
                        {[5, 10, 20, 50].map(s => (
                          <option key={s} value={s}>{s}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
                  {results.hits?.map((hit, i) => (
                    <StoryCard key={i} hit={hit} onMoreLikeThis={w => setSimilarWork(w)} />
                  ))}
                </div>

                {/* Pagination Controls */}
                {Math.ceil(results.total / size) > 1 && (
                  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 12, marginTop: 40, paddingBottom: 40 }}>
                    <button
                      disabled={page === 1}
                      onClick={() => handleSearch(null, page - 1, size)}
                      style={{
                        padding: '10px 20px', borderRadius: 9999,
                        border: '1px solid var(--color-border-light)',
                        backgroundColor: page === 1 ? 'transparent' : '#fff',
                        color: page === 1 ? '#cbd5e1' : 'var(--color-on-surface)',
                        fontSize: 12, fontWeight: 700,
                        cursor: page === 1 ? 'not-allowed' : 'pointer',
                        transition: 'all 0.2s',
                        boxShadow: page === 1 ? 'none' : '0 4px 12px rgba(0,0,0,0.03)',
                      }}
                    >
                      Previous
                    </button>

                    <div style={{ display: 'flex', gap: 6 }}>
                      {Array.from({ length: Math.ceil(results.total / size) }).map((_, i) => {
                        const pageNum = i + 1;
                        const maxPages = Math.ceil(results.total / size);
                        if (pageNum === 1 || pageNum === maxPages || Math.abs(pageNum - page) <= 1) {
                          return (
                            <button
                              key={pageNum}
                              onClick={() => handleSearch(null, pageNum, size)}
                              style={{
                                width: 36, height: 36, borderRadius: 9999,
                                border: page === pageNum ? 'none' : '1px solid var(--color-border-light)',
                                backgroundColor: page === pageNum ? 'var(--color-primary)' : '#fff',
                                color: page === pageNum ? '#fff' : 'var(--color-on-surface)',
                                fontSize: 13, fontWeight: 700, cursor: 'pointer',
                                transition: 'all 0.2s',
                                boxShadow: '0 4px 12px rgba(0,0,0,0.03)',
                              }}
                            >
                              {pageNum}
                            </button>
                          );
                        }
                        if (pageNum === 2 || pageNum === maxPages - 1) {
                          return <span key={pageNum} style={{ alignSelf: 'center', color: '#94a3b8' }}>...</span>;
                        }
                        return null;
                      })}
                    </div>

                    <button
                      disabled={page === Math.ceil(results.total / size)}
                      onClick={() => handleSearch(null, page + 1, size)}
                      style={{
                        padding: '10px 20px', borderRadius: 9999,
                        border: '1px solid var(--color-border-light)',
                        backgroundColor: page === Math.ceil(results.total / size) ? 'transparent' : '#fff',
                        color: page === Math.ceil(results.total / size) ? '#cbd5e1' : 'var(--color-on-surface)',
                        fontSize: 12, fontWeight: 700,
                        cursor: page === Math.ceil(results.total / size) ? 'not-allowed' : 'pointer',
                        transition: 'all 0.2s',
                        boxShadow: page === Math.ceil(results.total / size) ? 'none' : '0 4px 12px rgba(0,0,0,0.03)',
                      }}
                    >
                      Next
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Empty / Initial State */}
            {!results && !loading && !error && !similarWork && (
              <div style={{ textAlign: 'center', padding: '80px 0 60px', color: 'var(--color-text-secondary)' }}>
                <BookOpen size={52} style={{ margin: '0 auto 16px', display: 'block', opacity: 0.2 }} />
                <p style={{ fontSize: 18, fontWeight: 600, marginBottom: 6, color: 'var(--color-on-surface)' }}>Start your discovery</p>
                <p style={{ fontSize: 14 }}>Type a description above and click Search.</p>
              </div>
            )}
          </section>
        </div>
      </main>

      {/* ── Footer ── */}
      <footer style={{
        borderTop: '1px solid var(--color-border-light)',
        backgroundColor: 'var(--color-background)',
        padding: '40px 32px',
      }}>
        <div style={{ maxWidth: 1440, margin: '0 auto', display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: 16 }}>
          <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 800, fontSize: 18, color: 'var(--color-on-surface)' }}>StorySeek</span>
          <nav style={{ display: 'flex', gap: 28 }}>
            {['About', 'Privacy', 'Contact', 'API Docs'].map(l => (
              <a key={l} href="#" style={{ fontSize: 14, color: 'var(--color-text-secondary)', textDecoration: 'none', transition: 'color 0.2s' }}>{l}</a>
            ))}
          </nav>
          <span style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>© 2026 StorySeek. Trope-aware discovery.</span>
        </div>
      </footer>

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes float1 { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
        @keyframes float2 { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }
        @keyframes float3 { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-12px); } }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        a:hover { color: var(--color-on-surface) !important; }
      `}</style>
    </div>
  );
}
