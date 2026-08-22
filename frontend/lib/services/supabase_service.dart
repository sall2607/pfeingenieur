import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/equipment.dart';

class SupabaseService {

  static const String _url =
      'https://emjhbnszqikoxfydqnqz.supabase.co';
  static const String _key =
      'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9'
      '.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVtam'
      'hibnN6cWlrb3hmeWRxbnF6Iiwicm9sZSI6ImFub'
      '24iLCJpYXQiOjE3ODQ3MTk1MjksImV4cCI6MjEw'
      'MDI5NTUyOX0.ycJQZU46zrQhkvyMPS_lEacDvVO'
      'nqHpPtpuBAlK-WTI';

  static Map<String, String> get _headers => {
    'apikey':        _key,
    'Authorization': 'Bearer $_key',
    'Content-Type':  'application/json',
  };

  // Récupérer toutes les sessions
  static Future<List<Map<String, dynamic>>>
      getSessions() async {
    final r = await http.get(
      Uri.parse(
        '$_url/rest/v1/analysis_sessions'
        '?order=created_at.desc&limit=50'
      ),
      headers: _headers,
    );
    if (r.statusCode == 200) {
      return List<Map<String, dynamic>>.from(
          json.decode(r.body));
    }
    return [];
  }

  // Récupérer tous les équipements
  static Future<List<Map<String, dynamic>>>
      getEquipments() async {
    final r = await http.get(
      Uri.parse(
        '$_url/rest/v1/equipments'
        '?order=created_at.desc&limit=200'
      ),
      headers: _headers,
    );
    if (r.statusCode == 200) {
      return List<Map<String, dynamic>>.from(
          json.decode(r.body));
    }
    return [];
  }

  // Statistiques globales
  static Future<Map<String, dynamic>>
      getStats() async {
    final equipments = await getEquipments();
    final sessions   = await getSessions();

    // Compter par désignation
    final Map<String, int> byDesignation = {};
    int needsReviewCount = 0;

    for (final eq in equipments) {
      final d = eq['designation'] ?? 'Autres';
      byDesignation[d] = (byDesignation[d] ?? 0) + 1;
      if (eq['needs_review'] == true) {
        needsReviewCount++;
      }
    }

    // Temps moyen
    double avgTime = 0;
    if (sessions.isNotEmpty) {
      final times = sessions
          .where((s) => s['processing_time'] != null)
          .map((s) =>
              (s['processing_time'] as num).toDouble())
          .toList();
      if (times.isNotEmpty) {
        avgTime = times.reduce((a, b) => a + b)
                  / times.length;
      }
    }

    return {
      'total_equipments':  equipments.length,
      'total_sessions':    sessions.length,
      'needs_review':      needsReviewCount,
      'valid':             equipments.length
                           - needsReviewCount,
      'by_designation':    byDesignation,
      'avg_time':          avgTime,
    };
  }
}