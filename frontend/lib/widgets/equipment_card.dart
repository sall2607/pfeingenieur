import 'package:flutter/material.dart';
import '../models/equipment.dart';

class EquipmentCard extends StatelessWidget {
  final Equipment equipment;
  final VoidCallback onEdit;

  const EquipmentCard({
    super.key,
    required this.equipment,
    required this.onEdit,
  });

  @override
  Widget build(BuildContext context) {
    final e = equipment;
    final conf = e.confidence?['designation'] ?? 0.0;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(
          color: e.needsReview
              ? Colors.orange
              : Colors.green,
          width: 1.5,
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [

            // En-tête
            Row(
              children: [
                Text(e.icon,
                    style: const TextStyle(fontSize: 28)),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment:
                        CrossAxisAlignment.start,
                    children: [
                      Text(
                        e.name,
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 15,
                        ),
                      ),
                      Text(
                        e.designation,
                        style: TextStyle(
                          color: Colors.grey[600],
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
                // Badge statut
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: e.needsReview
                        ? Colors.orange[100]
                        : Colors.green[100],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    e.needsReview ? '⚠️ À réviser' : '✅ Valide',
                    style: TextStyle(
                      fontSize: 11,
                      color: e.needsReview
                          ? Colors.orange[800]
                          : Colors.green[800],
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),

            const Divider(height: 20),

            // Informations
            Wrap(
              spacing: 8,
              runSpacing: 6,
              children: [
                if (e.brand != null)
                  _chip(Icons.business, e.brand!),
                if (e.model != null)
                  _chip(Icons.label, e.model!),
                if (e.power != null)
                  _chip(Icons.bolt, '${e.power} W'),
                if (e.voltage != null)
                  _chip(Icons.electrical_services,
                      '${e.voltage} V'),
                if (e.temperature != null)
                  _chip(Icons.thermostat,
                      '${e.temperature}°C'),
                if (e.coolingCapacity != null)
                  _chip(Icons.ac_unit,
                      '${e.coolingCapacity} BTU'),
              ],
            ),

            const SizedBox(height: 8),

            // Confiance + bouton édition
            Row(
              children: [
                Icon(Icons.analytics,
                    size: 14, color: Colors.grey[500]),
                const SizedBox(width: 4),
                Text(
                  'Confiance : ${(conf * 100).toStringAsFixed(0)}%',
                  style: TextStyle(
                    fontSize: 11,
                    color: Colors.grey[600],
                  ),
                ),
                const Spacer(),
                if (e.needsReview)
                  TextButton.icon(
                    onPressed: onEdit,
                    icon: const Icon(Icons.edit, size: 14),
                    label: const Text('Corriger',
                        style: TextStyle(fontSize: 12)),
                    style: TextButton.styleFrom(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 4),
                    ),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _chip(IconData icon, String label) {
    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.grey[100],
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: Colors.grey[600]),
          const SizedBox(width: 4),
          Text(label,
              style: TextStyle(
                fontSize: 11,
                color: Colors.grey[700],
              )),
        ],
      ),
    );
  }
}