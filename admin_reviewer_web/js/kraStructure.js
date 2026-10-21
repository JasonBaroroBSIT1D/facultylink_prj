/**
 * Canonical FacultyLink KRA hierarchy (frontend specification).
 * KRA I–II: 3 criteria (A–C). KRA III–IV: 4 criteria (A–D). Total: 14 criteria.
 */
(function (global) {
  var KRA_META = [
    { id: 'kra1', key: 'KRA I', title: 'KRA I — Instruction', letters: ['A', 'B', 'C'] },
    { id: 'kra2', key: 'KRA II', title: 'KRA II — Research and Innovation', letters: ['A', 'B', 'C'] },
    {
      id: 'kra3',
      key: 'KRA III',
      title: 'KRA III — Extension or Community Services',
      letters: ['A', 'B', 'C', 'D'],
    },
    {
      id: 'kra4',
      key: 'KRA IV',
      title: 'KRA IV — Professional Development',
      letters: ['A', 'B', 'C', 'D'],
    },
  ]

  function lettersForKraKey(key) {
    var meta = KRA_META.find(function (k) {
      return k.key === key
    })
    return meta ? meta.letters.slice() : []
  }

  function shellCriterion(code) {
    return {
      code: code,
      title: 'Criterion ' + code,
      indicators: ['Indicators configured via backend'],
      evidence: ['Evidence requirements from institutional KRA config'],
      capNote: 'Mock configuration shell — official scoring from shared backend when connected.',
    }
  }

  var ADMIN_KRA_DETAILS = {
    kra1: {
      weightNote: 'Weighting configured per institutional guideline (mock).',
      criteria: {
        A: {
          code: 'A',
          title: 'Teaching Load & Quality',
          indicators: ['A.1 Student Evaluation (SET)', 'A.2 Supervisor Evaluation (SEF)', 'Teaching load compliance'],
          evidence: ['Official load form', 'SET aggregated report', 'SEF summary sheets'],
          capNote: 'SET and SEF belong under Criterion A (not separate criteria).',
        },
        B: {
          code: 'B',
          title: 'Course Development',
          indicators: ['Syllabus alignment', 'Learning materials'],
          evidence: ['Syllabus PDF', 'Module samples'],
          capNote: 'Scoring rules loaded from Flask API when available.',
        },
      },
    },
    kra2: {
      criteria: {
        A: {
          code: 'A',
          title: 'Research Output',
          indicators: ['Peer-reviewed publication', 'Citation index entry'],
          evidence: ['Publication PDF', 'Indexing proof'],
          capNote: 'Mock placeholder — no official CHED points displayed.',
        },
      },
    },
    kra3: {
      criteria: {
        A: {
          code: 'A',
          title: 'Community Extension',
          indicators: ['Extension project leadership', 'Beneficiary documentation'],
          evidence: ['MOA', 'Completion report'],
          capNote: 'Mock configuration shell only.',
        },
      },
    },
    kra4: {
      criteria: {
        A: {
          code: 'A',
          title: 'Advanced Studies & Certifications',
          indicators: ['Graduate degree', 'Professional license'],
          evidence: ['Diploma', 'PRC ID scan'],
          capNote: 'Evidence requirements editable when backend is connected.',
        },
      },
    },
  }

  function buildAdminKras() {
    return KRA_META.map(function (meta) {
      var detail = ADMIN_KRA_DETAILS[meta.id] || {}
      var criteria = meta.letters.map(function (letter) {
        var existing = detail.criteria && detail.criteria[letter]
        return existing || shellCriterion(letter)
      })
      return {
        id: meta.id,
        title: meta.title,
        weightNote: detail.weightNote || '',
        criteria: criteria,
      }
    })
  }

  function shellReviewerIndicator(code) {
    return {
      code: code,
      title: 'Indicator ' + code + ' (config TBD)',
      evidence: ['Supporting document'],
      aggregatedScore: 'Not Yet Calculated',
    }
  }

  function buildReviewerKras() {
    return KRA_META.map(function (meta) {
      var criteria = meta.letters.map(function (letter) {
        if (meta.id === 'kra1' && letter === 'A') {
          return {
            code: 'A',
            title: 'Criterion A — Teaching Effectiveness',
            indicators: [
              {
                code: 'A.1',
                title: 'Student Evaluation (SET)',
                evidence: ['Aggregated SET reports by academic year'],
                semesters: [
                  { term: '1st Sem AY 2024–2025', rating: 'Awaiting backend aggregation', duplicate: false },
                  { term: '2nd Sem AY 2024–2025', rating: 'Awaiting backend aggregation', duplicate: false },
                ],
                aggregatedScore: 'Not Yet Calculated',
                validation: 'Mock — display backend SET aggregation when integrated.',
              },
              {
                code: 'A.2',
                title: 'Supervisor Evaluation (SEF)',
                evidence: ['SEF summary sheets'],
                semesters: [
                  { term: '1st Sem AY 2024–2025', rating: 'Awaiting backend aggregation', duplicate: false },
                ],
                aggregatedScore: 'Not Yet Calculated',
                validation: 'Mock — semesters shown for review; final indicator score from backend.',
              },
            ],
          }
        }
        if (meta.id === 'kra1' && letter === 'B') {
          return {
            code: 'B',
            title: 'Criterion B — Load-related indicators',
            indicators: [
              {
                code: 'B.1',
                title: 'Teaching load compliance (placeholder)',
                evidence: ['Load form'],
                aggregatedScore: '—',
              },
            ],
          }
        }
        return {
          code: letter,
          title: 'Criterion ' + letter,
          indicators: [shellReviewerIndicator(letter + '.1')],
        }
      })
      return { id: meta.id, title: meta.title, criteria: criteria }
    })
  }

  global.FacultyLinkKraStructure = {
    meta: KRA_META,
    lettersForKraKey: lettersForKraKey,
    buildAdminKras: buildAdminKras,
    buildReviewerKras: buildReviewerKras,
  }
})(window)
