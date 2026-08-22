import 'package:flutter/material.dart';
import '../services/supabase_service.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() =>
      _DashboardScreenState();
}

class _DashboardScreenState
    extends State<DashboardScreen> {

  Map<String, dynamic> _stats   = {};
  List<Map<String, dynamic>> _sessions = [];
  bool _loading = true;

  // Icônes par désignation
  static const Map<String, String> _icons = {
    'AppareilCuisine':        '🍳',
    'AppareilInformatique':   '💻',
    'Climatisation':          '❄️',
    'Eclairage':              '💡',
    'Robinet':                '🚿',
    'Refrigeration':          '🧊',
    'PeripheriqueImpression': '🖨️',
    'InfrastructureIT':       '🌐',
    'Autres':                 '📦',
  };

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final stats    = await SupabaseService.getStats();
      final sessions = await SupabaseService.getSessions();
      setState(() {
        _stats    = stats;
        _sessions = sessions;
        _loading  = false;
      });
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Tableau de bord'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _load,
          ),
        ],
      ),
      body: _loading
          ? const Center(
              child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: SingleChildScrollView(
                physics:
                    const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment:
                      CrossAxisAlignment.stretch,
                  children: [

                    // ── KPIs principaux ──────────
                    _buildKPIs(),
                    const SizedBox(height: 20),

                    // ── Répartition par type ─────
                    _buildDesignationChart(),
                    const SizedBox(height: 20),

                    // ── Sessions récentes ────────
                    _buildRecentSessions(),
                  ],
                ),
              ),
            ),
    );
  }

  // ── KPIs ───────────────────────────────────────
  Widget _buildKPIs() {
    final total   = _stats['total_equipments'] ?? 0;
    final valid   = _stats['valid'] ?? 0;
    final review  = _stats['needs_review'] ?? 0;
    final sessions= _stats['total_sessions'] ?? 0;
    final avgTime = (_stats['avg_time'] ?? 0.0)
                    as double;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Vue d\'ensemble',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: Color(0xFF1565C0),
            )),
        const SizedBox(height: 12),
        Row(children: [
          Expanded(child: _kpiCard(
            icon:  Icons.inventory_2,
            label: 'Équipements',
            value: '$total',
            color: const Color(0xFF1565C0),
          )),
          const SizedBox(width: 8),
          Expanded(child: _kpiCard(
            icon:  Icons.check_circle,
            label: 'Valides',
            value: '$valid',
            color: Colors.green,
          )),
        ]),
        const SizedBox(height: 8),
        Row(children: [
          Expanded(child: _kpiCard(
            icon:  Icons.warning,
            label: 'À réviser',
            value: '$review',
            color: Colors.orange,
          )),
          const SizedBox(width: 8),
          Expanded(child: _kpiCard(
            icon:  Icons.timer,
            label: 'Temps moyen',
            value: '${avgTime.toStringAsFixed(1)}s',
            color: Colors.purple,
          )),
        ]),
        const SizedBox(height: 8),
        _kpiCard(
          icon:  Icons.videocam,
          label: 'Sessions d\'analyse',
          value: '$sessions',
          color: Colors.teal,
          fullWidth: true,
        ),
      ],
    );
  }

  Widget _kpiCard({
    required IconData icon,
    required String   label,
    required String   value,
    required Color    color,
    bool fullWidth = false,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color:        color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
            color: color.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          Icon(icon, color: color, size: 28),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment:
                CrossAxisAlignment.start,
            children: [
              Text(value,
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    color: color,
                  )),
              Text(label,
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey[600],
                  )),
            ],
          ),
        ],
      ),
    );
  }

  // ── Répartition par désignation ─────────────────
  Widget _buildDesignationChart() {
    final Map<String, int> byDes =
        Map<String, int>.from(
            _stats['by_designation'] ?? {});
    if (byDes.isEmpty) return const SizedBox();

    final total = byDes.values
        .fold(0, (a, b) => a + b);
    final sorted = byDes.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Répartition par type',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: Color(0xFF1565C0),
            )),
        const SizedBox(height: 12),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color:        Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
                color: Colors.grey.shade200),
            boxShadow: [
              BoxShadow(
                color:       Colors.grey.shade100,
                blurRadius:  8,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Column(
            children: sorted.map((entry) {
              final pct = total > 0
                  ? entry.value / total
                  : 0.0;
              final icon =
                  _icons[entry.key] ?? '📦';
              return Padding(
                padding: const EdgeInsets.only(
                    bottom: 12),
                child: Column(
                  crossAxisAlignment:
                      CrossAxisAlignment.start,
                  children: [
                    Row(children: [
                      Text(icon,
                          style: const TextStyle(
                              fontSize: 16)),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          entry.key,
                          style: const TextStyle(
                              fontSize: 13),
                          overflow:
                              TextOverflow.ellipsis,
                        ),
                      ),
                      Text(
                        '${entry.value} '
                        '(${(pct*100).toStringAsFixed(0)}%)',
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey[600],
                          fontWeight:
                              FontWeight.w500,
                        ),
                      ),
                    ]),
                    const SizedBox(height: 4),
                    LinearProgressIndicator(
                      value: pct,
                      backgroundColor:
                          Colors.grey[200],
                      valueColor:
                          const AlwaysStoppedAnimation(
                              Color(0xFF1565C0)),
                      minHeight: 6,
                      borderRadius:
                          BorderRadius.circular(3),
                    ),
                  ],
                ),
              );
            }).toList(),
          ),
        ),
      ],
    );
  }

  // ── Sessions récentes ───────────────────────────
  Widget _buildRecentSessions() {
    if (_sessions.isEmpty) return const SizedBox();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Sessions récentes',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: Color(0xFF1565C0),
            )),
        const SizedBox(height: 12),
        ..._sessions.take(10).map((s) {
          final time =
              (s['processing_time'] as num?)
              ?.toStringAsFixed(1) ?? '?';
          final total =
              s['total_equipment'] ?? 0;
          final valid =
              s['valid_count'] ?? 0;
          final loc =
              s['location'] ?? 'Inconnu';
          final date = s['created_at'] != null
              ? DateTime.parse(s['created_at'])
                  .toLocal()
                  .toString()
                  .substring(0, 16)
              : '?';

          return Card(
            margin: const EdgeInsets.only(
                bottom: 8),
            shape: RoundedRectangleBorder(
              borderRadius:
                  BorderRadius.circular(10),
            ),
            child: ListTile(
              leading: CircleAvatar(
                backgroundColor:
                    const Color(0xFF1565C0)
                    .withOpacity(0.1),
                child: const Icon(
                  Icons.videocam,
                  color: Color(0xFF1565C0),
                  size: 20,
                ),
              ),
              title: Text(
                loc,
                style: const TextStyle(
                  fontWeight: FontWeight.w600,
                  fontSize: 14,
                ),
              ),
              subtitle: Text(
                '$date  •  ${time}s',
                style: TextStyle(
                  fontSize: 11,
                  color: Colors.grey[600],
                ),
              ),
              trailing: Column(
                mainAxisAlignment:
                    MainAxisAlignment.center,
                children: [
                  Text(
                    '$valid/$total',
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      color: Colors.green,
                      fontSize: 14,
                    ),
                  ),
                  const Text(
                    'valides',
                    style: TextStyle(
                      fontSize: 10,
                      color: Colors.grey,
                    ),
                  ),
                ],
              ),
            ),
          );
        }),
      ],
    );
  }
}