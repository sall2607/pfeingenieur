import 'package:flutter/material.dart';
import 'screens/home_screen.dart';
import 'services/auth_service.dart';
import 'screens/login_screen.dart';

void main() {
  runApp(const SFMEquipmentApp());
}

class SFMEquipmentApp extends StatelessWidget {
  const SFMEquipmentApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SFM Equipment',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF1565C0),
          brightness: Brightness.light,
        ),
        useMaterial3: true,
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF1565C0),
          foregroundColor: Colors.white,
          elevation: 2,
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF1565C0),
            foregroundColor: Colors.white,
            padding: const EdgeInsets.symmetric(
              horizontal: 24, vertical: 14),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
          ),
        ),
      ),
      home: const AuthGate(),  // ← changer ici
    );
  }
}


// Vérification automatique de la session
class AuthGate extends StatefulWidget {
  const AuthGate({super.key});

  @override
  State<AuthGate> createState() =>
      _AuthGateState();
}

class _AuthGateState extends State<AuthGate> {

  @override
  void initState() {
    super.initState();
    _check();
  }

  Future<void> _check() async {
    final loggedIn = await AuthService.isLoggedIn();
    if (!mounted) return;
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (_) => loggedIn
            ? const HomeScreen()
            : const LoginScreen(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      backgroundColor: Color(0xFF1565C0),
      body: Center(
        child: CircularProgressIndicator(
          color: Colors.white),
      ),
    );
  }
}