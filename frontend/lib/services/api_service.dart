import 'dart:io';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/equipment.dart';

class ApiService {

  // ⚠️ Remplacez par l'IP de votre PC sur le réseau Wi-Fi local
  // Exemple : 192.168.1.45:8000
  static const String _baseUrl = 'http://192.168.1.210:8000';

  // Health check
  static Future<bool> healthCheck() async {
    try {
      final response = await http
          .get(Uri.parse('$_baseUrl/api/health'))
          .timeout(const Duration(seconds: 10));
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  // Login
  static Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/api/auth/login'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'email':    email,
          'password': password,
        }),
      );

      if (response.statusCode == 200) {
        return {
          'success': true,
          'user': json.decode(response.body)['user'],
        };
    } else {
        final error = json.decode(response.body);
        return {
          'success': false,
          'error': error['detail'] ??
                  'Connexion échouée',
        };
    }
  } catch (e) {
    return {
      'success': false,
      'error': 'Serveur inaccessible',
    };
  }
}

  // Récupérer quota
  static Future<Map<String, dynamic>>
      getQuota(String userId) async {
    try {
      final r = await http.get(
        Uri.parse('$_baseUrl/api/quota/$userId'),
      );
      if (r.statusCode == 200) {
        return json.decode(r.body);
      }
    } catch (e) {
      // ignore
    }
    return {'remaining': 0, 'can_analyze': false};
  }

  // Analyser une vidéo
  static Future<Map<String, dynamic>> analyzeVideo({
    required File videoFile,
    required String location,
    int maxKeyframes = 15,
    String? userId,
  }) async {
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$_baseUrl/api/analyze-video'),
    );

    request.fields['location']      = location;
    request.fields['max_keyframes'] = maxKeyframes.toString();

    // ← AJOUTER CES LIGNES
    if (userId != null) {
      request.fields['user_id'] = userId;
    }


    request.files.add(
      await http.MultipartFile.fromPath(
        'file',
        videoFile.path,
        filename: 'video.mp4',
      ),
    );

    try {
      final streamedResponse = await request.send()
          .timeout(const Duration(seconds: 180));
      final response =
          await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return {
          'success':   true,
          'data':      data,
          'equipments': (data['equipments'] as List)
              .map((e) => Equipment.fromJson(e))
              .toList(),
        };
      } else {
        return {
          'success': false,
          'error':   'Erreur HTTP ${response.statusCode}',
        };
      }
    } on SocketException {
      return {
        'success': false,
        'error':   'Impossible de joindre le serveur. '
                   'Vérifiez que le backend est démarré.',
      };
    } catch (e) {
      return {
        'success': false,
        'error':   e.toString(),
      };
    }
  }

  // Récupérer l'IP locale du PC
  // À afficher dans les paramètres de l'app
  static String get serverUrl => _baseUrl;
}