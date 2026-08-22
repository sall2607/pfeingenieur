import 'package:flutter/material.dart';
import '../models/equipment.dart';
import '../widgets/equipment_card.dart';
import 'edit_screen.dart';
import 'home_screen.dart';

class ResultsScreen extends StatefulWidget {
  final List<Equipment> equipments;
  final String          location;
  final double          processingTime;
  final Map<String, dynamic> metadata;

  const ResultsScreen({
    super.key,
    required this.equipments,
    required this.location,
    required this.processingTime,
    required this.metadata,
  });

  @override
  State<ResultsScreen> createState() => _ResultsScreenState();
}

class _ResultsScreenState extends State<ResultsScreen> {

  late List<Equipment> _equipments;

  @override
  void initState() {
    super.initState();
    _equipments = List.from(widget.equipments);
  }

  int get _validCount =>
      _equipments.where((e) => !e.needsReview).length;
  int get _reviewCount =>
      _equipments.where((e) => e.needsReview).length;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Résultats'),
        leading: IconButton(
          icon: const Icon(Icons.home),
          onPressed: () => Navigator.pushAndRemoveUntil(
            context,
            MaterialPageRoute(
                builder: (_) => const HomeScreen()),
            (r) => false,
          ),
        ),
      ),
      body: Column(
        children: [

          // Bandeau résumé
          _buildSummary(),

          // Liste fiches
          Expanded(
            child: _equipments.isEmpty
                ? _buildEmpty()
                : ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _equipments.length,
                    itemBuilder: (ctx, i) => EquipmentCard(
                      equipment: _equipments[i],
                      onEdit: () => _openEdit(i),
                    ),
                  ),
          ),
        ],
      ),
      bottomNavigationBar: _buildBottomBar(),
    );
  }

  Widget _buildSummary() {
    return Container(
      padding: const EdgeInsets.all(16),
      color: const Color(0xFF1565C0),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildStat(
                  '${_equipments.length}',
                  'Total',
                  Icons.inventory_2),
              _buildStat(
                  '$_validCount',
                  'Valides',
                  Icons.check_circle,
                  color: Colors.greenAccent),
              _buildStat(
                  '$_reviewCount',
                  'À réviser',
                  Icons.warning,
                  color: Colors.orangeAccent),
              _buildStat(
                  '${widget.processingTime.toStringAsFixed(0)}s',
                  'Durée',
                  Icons.timer),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            widget.location,
            style: const TextStyle(
              color: Colors.white70,
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStat(String value, String label,
      IconData icon, {Color color = Colors.white}) {
    return Column(
      children: [
        Icon(icon, color: color, size: 22),
        const SizedBox(height: 4),
        Text(value,
            style: TextStyle(
              color: color,
              fontSize: 20,
              fontWeight: FontWeight.bold,
            )),
        Text(label,
            style: const TextStyle(
              color: Colors.white70,
              fontSize: 11,
            )),
      ],
    );
  }

  Widget _buildEmpty() {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.search_off, size: 64, color: Colors.grey),
          SizedBox(height: 16),
          Text(
            'Aucun équipement détecté',
            style: TextStyle(
              fontSize: 18, color: Colors.grey),
          ),
          SizedBox(height: 8),
          Text(
            'Essayez de filmer plus près des équipements',
            style: TextStyle(
              fontSize: 13, color: Colors.grey),
          ),
        ],
      ),
    );
  }

  Widget _buildBottomBar() {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: ElevatedButton.icon(
          onPressed: () => Navigator.pushAndRemoveUntil(
            context,
            MaterialPageRoute(
                builder: (_) => const HomeScreen()),
            (r) => false,
          ),
          icon: const Icon(Icons.add_circle),
          label: const Text('Nouvelle analyse'),
          style: ElevatedButton.styleFrom(
            padding: const EdgeInsets.symmetric(vertical: 14),
          ),
        ),
      ),
    );
  }

  Future<void> _openEdit(int index) async {
    final updated = await Navigator.push<Equipment>(
      context,
      MaterialPageRoute(
        builder: (_) =>
            EditScreen(equipment: _equipments[index]),
      ),
    );
    if (updated != null) {
      setState(() => _equipments[index] = updated);
    }
  }
}