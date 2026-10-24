/// KRA configuration from GET /api/v1/kra-configuration (no hardcoded DB ids).
class KraCriterionTarget {
  const KraCriterionTarget({
    required this.kraId,
    required this.kraCode,
    required this.kraName,
    required this.criterionId,
    required this.criterionCode,
    required this.criterionName,
  });

  final int kraId;
  final String kraCode;
  final String kraName;
  final int criterionId;
  final String criterionCode;
  final String criterionName;

  String get displayLabel => '$kraCode — Criterion $criterionCode';
}

class KraConfigurationBundle {
  const KraConfigurationBundle({required this.kras});

  final List<Map<String, dynamic>> kras;

  factory KraConfigurationBundle.fromJson(Map<String, dynamic> json) {
    return KraConfigurationBundle(
      kras: (json['kras'] as List<dynamic>? ?? [])
          .map((e) => e as Map<String, dynamic>)
          .toList(),
    );
  }

  KraCriterionTarget? findCriterion({
    required String kraCode,
    required String criterionCode,
  }) {
    for (final kra in kras) {
      if ((kra['code'] as String?)?.trim() != kraCode) continue;
      for (final c in (kra['criteria'] as List<dynamic>? ?? [])) {
        final crit = c as Map<String, dynamic>;
        if ((crit['code'] as String?)?.trim() == criterionCode) {
          return KraCriterionTarget(
            kraId: kra['kra_id'] as int,
            kraCode: kra['code'] as String,
            kraName: kra['name'] as String? ?? kraCode,
            criterionId: crit['criterion_id'] as int,
            criterionCode: crit['code'] as String,
            criterionName: crit['name'] as String? ?? criterionCode,
          );
        }
      }
    }
    return null;
  }

  KraCriterionTarget? get kraICriterionA =>
      findCriterion(kraCode: 'KRA I', criterionCode: 'A');

  String? indicatorLabelFor(int? indicatorId) {
    if (indicatorId == null) return null;
    for (final kra in kras) {
      for (final c in (kra['criteria'] as List<dynamic>? ?? [])) {
        final crit = c as Map<String, dynamic>;
        for (final ind in (crit['indicators'] as List<dynamic>? ?? [])) {
          final row = ind as Map<String, dynamic>;
          if (row['indicator_id'] == indicatorId) {
            final code = row['code'] as String? ?? '';
            final name = row['name'] as String? ?? '';
            return code.isEmpty ? name : '$code — $name';
          }
        }
      }
    }
    return null;
  }

  KraCriterionTarget? criterionForId(int? criterionId) {
    if (criterionId == null) return null;
    for (final kra in kras) {
      for (final c in (kra['criteria'] as List<dynamic>? ?? [])) {
        final crit = c as Map<String, dynamic>;
        if (crit['criterion_id'] == criterionId) {
          return KraCriterionTarget(
            kraId: kra['kra_id'] as int,
            kraCode: kra['code'] as String,
            kraName: kra['name'] as String? ?? '',
            criterionId: crit['criterion_id'] as int,
            criterionCode: crit['code'] as String,
            criterionName: crit['name'] as String? ?? '',
          );
        }
      }
    }
    return null;
  }
}
