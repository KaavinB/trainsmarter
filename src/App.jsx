import { useState, useEffect, useRef } from 'react';
import './App.css';

// === CONSTANTS ===
const API_BASE = 'http://localhost:8000/api';

// === DIFFICULTY FILTERS ===
const DIFFICULTY_FILTERS = ['beginner', 'intermediate', 'expert'];
const EQUIPMENT_FILTERS = ['dumbbell', 'barbell', 'body weight', 'cable', 'machine', 'kettlebell', 'band'];

// === COMPONENTS ===

// Loading skeleton for exercise cards
function SkeletonCard() {
  return (
    <div className="skeleton-card">
      <div className="skeleton-image"></div>
      <div className="skeleton-content">
        <div className="skeleton-title"></div>
        <div className="skeleton-line"></div>
        <div className="skeleton-line"></div>
        <div className="skeleton-line"></div>
      </div>
    </div>
  );
}

// Exercise card component
function ExerciseCard({ exercise }) {
  const [showInstructions, setShowInstructions] = useState(false);

  // Get image URL from backend (includes full CDN path)
  const imageUrl = exercise.imageUrl || null;

  // Format muscle display - handle both array and string formats
  const primaryMuscles = Array.isArray(exercise.primaryMuscles)
    ? exercise.primaryMuscles.join(', ')
    : (exercise.primaryMuscles || 'N/A');
  const secondaryMuscles = exercise.secondaryMuscles?.length > 0
    ? (Array.isArray(exercise.secondaryMuscles) ? exercise.secondaryMuscles.join(', ') : exercise.secondaryMuscles)
    : null;

  return (
    <div className="exercise-card">
      <div className="exercise-image-container">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={exercise.name}
            className="exercise-image"
            onError={(e) => {
              e.target.style.display = 'none';
            }}
          />
        ) : (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            fontSize: '48px'
          }}>
            🏋️
          </div>
        )}
        <span className={`exercise-level-badge ${exercise.level}`}>
          {exercise.level}
        </span>
        {/* YouTube Video Button Overlay */}
        {exercise.youtubeSearchUrl && (
          <a
            href={exercise.youtubeSearchUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="youtube-video-btn"
            title="Watch exercise tutorial on YouTube"
          >
            <span className="youtube-icon">▶</span>
            <span className="youtube-text">Watch Tutorial</span>
          </a>
        )}
      </div>

      <div className="exercise-content">
        <h3 className="exercise-name">{exercise.name}</h3>

        <div className="exercise-meta">
          <span className="meta-tag">
            <span className="emoji">💪</span>
            {primaryMuscles}
          </span>
          {secondaryMuscles && (
            <span className="meta-tag">
              <span className="emoji">🎯</span>
              {secondaryMuscles}
            </span>
          )}
          {exercise.equipment && (
            <span className="meta-tag">
              <span className="emoji">🏋️</span>
              {exercise.equipment}
            </span>
          )}
        </div>

        <div className="sets-reps">
          <div className="sets-reps-item">
            <div className="sets-reps-value">{exercise.sets || 3}</div>
            <div className="sets-reps-label">Sets</div>
          </div>
          <div className="sets-reps-item">
            <div className="sets-reps-value">{exercise.reps || '10-12'}</div>
            <div className="sets-reps-label">Reps</div>
          </div>
          <div className="sets-reps-item">
            <div className="sets-reps-value">{exercise.restSeconds || 60}s</div>
            <div className="sets-reps-label">Rest</div>
          </div>
        </div>

        {exercise.trainerNotes && (
          <div style={{
            padding: '12px',
            background: 'var(--accent-dim)',
            borderRadius: 'var(--radius-md)',
            marginBottom: '16px',
            fontSize: '13px',
            color: 'var(--text-secondary)'
          }}>
            <strong style={{ color: 'var(--accent)' }}>💡 Trainer Tip:</strong> {exercise.trainerNotes}
          </div>
        )}

        {exercise.instructions?.length > 0 && (
          <>
            <button
              className={`instructions-toggle ${showInstructions ? 'open' : ''}`}
              onClick={() => setShowInstructions(!showInstructions)}
            >
              <span>Step-by-Step Instructions</span>
              <span className="toggle-icon">▼</span>
            </button>
            <div className={`instructions-content ${showInstructions ? 'open' : ''}`}>
              <ol className="instructions-list">
                {exercise.instructions.map((instruction, idx) => (
                  <li key={idx}>{instruction}</li>
                ))}
              </ol>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// Workout Summary Card
function WorkoutSummary({ plan }) {
  return (
    <div className="workout-summary">
      <div className="summary-header">
        <div className="summary-icon">🏆</div>
        <h2 className="summary-title">{plan.workout_focus || 'Your Personalized Workout'}</h2>
      </div>

      <p className="summary-content">{plan.summary}</p>

      <div className="summary-stats">
        <div className="stat-item">
          <span className="stat-icon">⏱️</span>
          <span className="stat-text">Duration: <span className="stat-value">{plan.estimated_time || '45 min'}</span></span>
        </div>
        <div className="stat-item">
          <span className="stat-icon">📊</span>
          <span className="stat-text">Difficulty: <span className="stat-value">{plan.difficulty || 'Intermediate'}</span></span>
        </div>
        <div className="stat-item">
          <span className="stat-icon">🔢</span>
          <span className="stat-text">Exercises: <span className="stat-value">{plan.exercises?.length || 0}</span></span>
        </div>
      </div>

      {(plan.warmup_recommendation || plan.cooldown_recommendation) && (
        <div style={{
          marginTop: '20px',
          paddingTop: '20px',
          borderTop: '1px solid var(--border-subtle)',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px'
        }}>
          {plan.warmup_recommendation && (
            <div>
              <strong style={{ color: 'var(--accent)', fontSize: '12px', letterSpacing: '1px' }}>🔥 WARM-UP</strong>
              <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '8px' }}>
                {plan.warmup_recommendation}
              </p>
            </div>
          )}
          {plan.cooldown_recommendation && (
            <div>
              <strong style={{ color: 'var(--accent)', fontSize: '12px', letterSpacing: '1px' }}>❄️ COOL-DOWN</strong>
              <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '8px' }}>
                {plan.cooldown_recommendation}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// === MAIN APP COMPONENT ===
function App() {
  // State
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [backendStatus, setBackendStatus] = useState('checking');
  const [workoutPlan, setWorkoutPlan] = useState(null);
  const [exercises, setExercises] = useState([]);
  const [error, setError] = useState(null);
  const [selectedDifficulty, setSelectedDifficulty] = useState(null);
  const [selectedEquipment, setSelectedEquipment] = useState([]);

  // Check backend status on mount
  useEffect(() => {
    async function checkBackend() {
      try {
        const response = await fetch(`${API_BASE.replace('/api', '')}/`);
        if (response.ok) {
          setBackendStatus('connected');
        } else {
          setBackendStatus('error');
        }
      } catch {
        setBackendStatus('error');
      }
    }
    checkBackend();
  }, []);

  // Use ref for scrolling to results
  const resultsRef = useRef(null);

  // Handle form submission
  async function handleSubmit(e) {
    e.preventDefault();

    if (!query.trim()) {
      setError('Please describe your workout needs');
      return;
    }

    if (backendStatus !== 'connected') {
      setError('Backend server is not running. Please start it with: python backend/main.py');
      return;
    }

    setLoading(true);
    setError(null);
    setWorkoutPlan(null);
    setExercises([]);

    try {
      const response = await fetch(`${API_BASE}/workout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query,
          difficulty: selectedDifficulty,
          equipment: selectedEquipment.length > 0 ? selectedEquipment : null
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server Error: ${response.status}`);
      }

      const data = await response.json();
      setWorkoutPlan(data.plan);
      setExercises(data.exercises);

      // Smooth scroll to results after a short delay to allow rendering
      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);

    } catch (err) {
      console.error('Error:', err);
      setError(err.message || 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  // Toggle equipment filter
  function toggleEquipment(eq) {
    setSelectedEquipment(prev =>
      prev.includes(eq)
        ? prev.filter(e => e !== eq)
        : [...prev, eq]
    );
  }

  return (
    <div className="app-container">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-badge">
          <span>⚡</span>
          <span>AI-POWERED PERSONAL TRAINER</span>
        </div>

        <h1 className="hero-title">
          TRAIN
          <span className="accent">SMARTER</span>
        </h1>

        <p className="hero-subtitle">
          Describe your workout goals and let AI create a personalized exercise routine
          with 800+ exercises from the world's largest open exercise database.
        </p>



        {/* Search Form */}
        <form onSubmit={handleSubmit} className="search-container">
          <textarea
            className="search-textarea"
            placeholder="Describe your workout... (e.g., 'chest and triceps for beginners with dumbbells', 'full body strength workout using bodyweight', '30-minute leg day avoiding knee stress')"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={loading}
          />

          {/* Quick Filters */}
          <div className="quick-filters">
            <span style={{ fontSize: '12px', color: 'var(--text-muted)', marginRight: '8px' }}>Difficulty:</span>
            {DIFFICULTY_FILTERS.map(diff => (
              <button
                key={diff}
                type="button"
                className={`filter-chip ${selectedDifficulty === diff ? 'active' : ''}`}
                onClick={() => setSelectedDifficulty(selectedDifficulty === diff ? null : diff)}
              >
                {diff.charAt(0).toUpperCase() + diff.slice(1)}
              </button>
            ))}
          </div>

          <div className="quick-filters">
            <span style={{ fontSize: '12px', color: 'var(--text-muted)', marginRight: '8px' }}>Equipment:</span>
            {EQUIPMENT_FILTERS.slice(0, 5).map(eq => (
              <button
                key={eq}
                type="button"
                className={`filter-chip ${selectedEquipment.includes(eq) ? 'active' : ''}`}
                onClick={() => toggleEquipment(eq)}
              >
                {eq.charAt(0).toUpperCase() + eq.slice(1)}
              </button>
            ))}
          </div>

          <button
            type="submit"
            className="submit-btn"
            disabled={loading || !query.trim() || backendStatus !== 'connected'}
          >
            {loading ? 'GENERATING YOUR WORKOUT...' : 'BUILD MY WORKOUT'}
          </button>
        </form>

        {/* Backend Instructions */}
        {backendStatus === 'error' && (
          <div style={{
            marginTop: '24px',
            padding: '20px',
            background: 'var(--bg-card)',
            border: '1px solid #f8717133',
            borderRadius: 'var(--radius-md)',
            textAlign: 'left'
          }}>
            <h4 style={{ color: '#f87171', marginBottom: '12px', fontSize: '14px' }}>
              ⚠️ Backend Server Not Running
            </h4>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '12px' }}>
              Start the Python backend to enable AI workout generation:
            </p>
            <code style={{
              display: 'block',
              padding: '12px',
              background: 'var(--bg-secondary)',
              borderRadius: 'var(--radius-sm)',
              fontSize: '12px',
              color: 'var(--accent)',
              marginBottom: '8px'
            }}>
              cd backend && pip install -r requirements.txt
            </code>
            <code style={{
              display: 'block',
              padding: '12px',
              background: 'var(--bg-secondary)',
              borderRadius: 'var(--radius-sm)',
              fontSize: '12px',
              color: 'var(--accent)',
              marginBottom: '12px'
            }}>
              python main.py
            </code>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Don't forget to add your ANTHROPIC_API_KEY to backend/.env
            </p>
          </div>
        )}
      </section>

      {/* Loading State */}
      {loading && (
        <>
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <p className="loading-text">CRAFTING YOUR PERFECT WORKOUT</p>
            <p className="loading-subtext">Analyzing exercises and building your personalized routine...</p>
          </div>
          <div className="skeleton-grid">
            {[...Array(3)].map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        </>
      )}

      {/* Error State */}
      {error && !loading && (
        <div className="error-container">
          <div className="error-icon">⚠️</div>
          <h3 className="error-title">SOMETHING WENT WRONG</h3>
          <p className="error-message">{error}</p>
          <button className="retry-btn" onClick={() => setError(null)}>
            TRY AGAIN
          </button>
        </div>
      )}

      {/* Results */}
      {!loading && !error && workoutPlan && exercises.length > 0 && (
        <section className="results-section" ref={resultsRef}>
          <WorkoutSummary plan={workoutPlan} />

          <h2 className="exercises-title">YOUR EXERCISES</h2>

          <div className="exercises-grid">
            {exercises.slice(0, 3).map((exercise, index) => (
              <ExerciseCard
                key={exercise.id || index}
                exercise={exercise}
              />
            ))}
          </div>
        </section>
      )}

      {/* Empty State */}
      {!loading && !error && !workoutPlan && (
        <div className="empty-state">
          <div className="empty-icon">🎯</div>
          <h3 className="empty-title">READY WHEN YOU ARE</h3>
          <p className="empty-subtitle">
            Enter your workout goals above to get started with AI-powered exercise recommendations
          </p>
        </div>
      )}
    </div>
  );
}

export default App;
