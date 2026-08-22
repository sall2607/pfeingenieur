import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';

class AuthService {

  static Map<String, dynamic>? _currentUser;

  // Sauvegarder l'utilisateur connecté
  static Future<void> saveUser(
      Map<String, dynamic> user) async {
    _currentUser = user;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
        'current_user', json.encode(user));
  }

  // Récupérer l'utilisateur connecté
  static Future<Map<String, dynamic>?>
      getUser() async {
    if (_currentUser != null) return _currentUser;
    final prefs = await SharedPreferences.getInstance();
    final str   = prefs.getString('current_user');
    if (str != null) {
      _currentUser = json.decode(str);
      return _currentUser;
    }
    return null;
  }

  // Récupérer l'ID utilisateur
  static Future<String?> getUserId() async {
    final user = await getUser();
    return user?['id'];
  }

  // Vérifier si connecté
  static Future<bool> isLoggedIn() async {
    final user = await getUser();
    return user != null;
  }

  // Déconnexion
  static Future<void> logout() async {
    _currentUser = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('current_user');
  }

  // Nom de l'utilisateur
  static String get name =>
      _currentUser?['name'] ?? 'Utilisateur';

  // Rôle
  static String get role =>
      _currentUser?['role'] ?? 'technicien';

  // Est admin
  static bool get isAdmin => role == 'admin';
}