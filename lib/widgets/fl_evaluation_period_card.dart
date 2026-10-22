import 'package:flutter/material.dart';
import '../core/theme/app_colors.dart';
import '../models/evaluation_period.dart';
import '../services/evaluation_period_controller.dart';

class FlEvaluationPeriodCard extends StatefulWidget {
  const FlEvaluationPeriodCard({super.key, this.onSubmit, this.controller});
  final VoidCallback? onSubmit;
  final EvaluationPeriodController? controller;

  @override
  State<FlEvaluationPeriodCard> createState() => _FlEvaluationPeriodCardState();
}

class _FlEvaluationPeriodCardState extends State<FlEvaluationPeriodCard> {
  EvaluationPeriodController get controller =>
      widget.controller ?? EvaluationPeriodController.instance;

  @override
  void initState() {
    super.initState();
    if (widget.controller != null) return;
    if (controller.periods.isEmpty && controller.error == null && !controller.loading) {
      controller.load();
    }
  }

  String _statusLabel(EvaluationPeriodStatus? status) {
    return switch (status) {
      EvaluationPeriodStatus.upcoming => 'Upcoming',
      EvaluationPeriodStatus.open => 'Open',
      EvaluationPeriodStatus.closed => 'Closed',
      null => '—',
    };
  }

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
    animation: controller,
    builder: (context, _) {
      final period = controller.current;
      final status = period?.statusAt(controller.now);
      return Card(
        margin: EdgeInsets.zero,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  const Icon(
                    Icons.date_range_outlined,
                    color: AppColors.primaryBlue,
                    size: 22,
                  ),
                  const SizedBox(width: 10),
                  const Expanded(
                    child: Text(
                      'Evaluation Period',
                      style: TextStyle(
                        fontWeight: FontWeight.w700,
                        color: AppColors.primaryNavy,
                      ),
                    ),
                  ),
                ],
              ),
              if (controller.loading) ...[
                const SizedBox(height: 14),
                const LinearProgressIndicator(),
              ] else if (controller.error != null) ...[
                const SizedBox(height: 12),
                Text(controller.error!),
                TextButton(
                  onPressed: controller.load,
                  child: const Text('Try again'),
                ),
              ] else if (period == null) ...[
                const SizedBox(height: 12),
                const Text(
                  'No evaluation period is configured. Submissions are unavailable.',
                ),
              ] else ...[
                const SizedBox(height: 14),
                _InfoRow(
                  label: 'Evaluation cycle',
                  value: period.academicYear,
                ),
                const SizedBox(height: 8),
                _InfoRow(
                  label: 'Opening',
                  value: EvaluationPeriod.formatManila(period.opensAt),
                ),
                const SizedBox(height: 8),
                _InfoRow(
                  label: 'Closing',
                  value: EvaluationPeriod.formatManila(period.closesAt),
                ),
                const SizedBox(height: 8),
                _InfoRow(
                  label: 'Status',
                  value: _statusLabel(status),
                  emphasized: true,
                ),
                const SizedBox(height: 10),
                Text(
                  controller.canSubmit
                      ? 'Submissions are permitted while the period is open.'
                      : status == EvaluationPeriodStatus.upcoming
                      ? 'Submissions will be available when the period opens.'
                      : status == EvaluationPeriodStatus.closed
                      ? 'Submissions are closed. You can still view documents and KRA assessment.'
                      : 'Submissions are paused for this period.',
                  style: const TextStyle(
                    fontSize: 12,
                    color: AppColors.textMuted,
                  ),
                ),
                if (widget.onSubmit != null && controller.canSubmit) ...[
                  const SizedBox(height: 12),
                  FilledButton.icon(
                    onPressed: widget.onSubmit,
                    icon: const Icon(Icons.upload_file, size: 18),
                    label: const Text('Submit Documents'),
                  ),
                ],
              ],
              const SizedBox(height: 8),
              const Text(
                'Asia/Manila (UTC+8)',
                style: TextStyle(fontSize: 10, color: AppColors.textMuted),
              ),
            ],
          ),
        ),
      );
    },
  );
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({
    required this.label,
    required this.value,
    this.emphasized = false,
  });

  final String label;
  final String value;
  final bool emphasized;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 118,
          child: Text(
            label,
            style: const TextStyle(fontSize: 12, color: AppColors.textMuted),
          ),
        ),
        Expanded(
          child: Text(
            value,
            style: TextStyle(
              fontSize: 12,
              fontWeight: emphasized ? FontWeight.w700 : FontWeight.w500,
              color: emphasized ? AppColors.primaryBlue : AppColors.primaryNavy,
            ),
          ),
        ),
      ],
    );
  }
}
