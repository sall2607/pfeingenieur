import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import 'home_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() =>
      _LoginScreenState();
}

class _LoginScreenState
    extends State<LoginScreen> {

  final _emailCtrl    = TextEditingController();
  final _passwordCtrl = TextEditingController();
  bool  _loading      = false;
  bool  _obscure      = true;
  String? _error;

  Future<void> _login() async {
    if (_emailCtrl.text.isEmpty ||
        _passwordCtrl.text.isEmpty) {
      setState(() =>
          _error = 'Remplissez tous les champs');
      return;
    }

    setState(() { _loading = true; _error = null; });

    try {
      final result = await ApiService.login(
        email:    _emailCtrl.text.trim(),
        password: _passwordCtrl.text,
      );

      if (result['success'] == true) {
        // Sauvegarder l'utilisateur
        await AuthService.saveUser(result['user']);

        if (mounted) {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(
              builder: (_) => const HomeScreen()),
          );
        }
      } else {
        setState(() =>
            _error = result['error'] ??
            'Connexion échouée');
      }
    } catch (e) {
      setState(() =>
          _error = 'Erreur : $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF1565C0),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment:
                  MainAxisAlignment.center,
              children: [

                // Logo
                const Icon(Icons.business,
                    size: 72,
                    color: Colors.white),
                const SizedBox(height: 16),
                const Text(
                  'SFM Technologies',
                  style: TextStyle(
                    fontSize: 26,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Détection automatique d\'équipements',
                  style: TextStyle(
                    fontSize: 13,
                    color: Colors.white70,
                  ),
                  textAlign: TextAlign.center,
                ),

                const SizedBox(height: 40),

                // Carte de connexion
                Container(
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius:
                        BorderRadius.circular(16),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black
                            .withOpacity(0.1),
                        blurRadius: 20,
                      ),
                    ],
                  ),
                  child: Column(
                    crossAxisAlignment:
                        CrossAxisAlignment.stretch,
                    children: [

                      const Text(
                        'Connexion',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF1565C0),
                        ),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 24),

                      // Email
                      TextFormField(
                        controller: _emailCtrl,
                        keyboardType:
                            TextInputType.emailAddress,
                        decoration: InputDecoration(
                          labelText: 'Email',
                          prefixIcon: const Icon(
                              Icons.email),
                          border: OutlineInputBorder(
                            borderRadius:
                                BorderRadius.circular(
                                    8)),
                          filled:     true,
                          fillColor:  Colors.grey[50],
                        ),
                      ),
                      const SizedBox(height: 16),

                      // Mot de passe
                      TextFormField(
                        controller: _passwordCtrl,
                        obscureText: _obscure,
                        decoration: InputDecoration(
                          labelText: 'Mot de passe',
                          prefixIcon: const Icon(
                              Icons.lock),
                          suffixIcon: IconButton(
                            icon: Icon(_obscure
                                ? Icons.visibility
                                : Icons.visibility_off),
                            onPressed: () => setState(
                                () => _obscure =
                                    !_obscure),
                          ),
                          border: OutlineInputBorder(
                            borderRadius:
                                BorderRadius.circular(
                                    8)),
                          filled:    true,
                          fillColor: Colors.grey[50],
                        ),
                      ),

                      // Erreur
                      if (_error != null) ...[
                        const SizedBox(height: 12),
                        Container(
                          padding: const EdgeInsets
                              .all(10),
                          decoration: BoxDecoration(
                            color: Colors.red[50],
                            borderRadius:
                                BorderRadius.circular(
                                    8),
                            border: Border.all(
                                color: Colors.red
                                    .shade200),
                          ),
                          child: Row(children: [
                            const Icon(Icons.error,
                                color: Colors.red,
                                size: 16),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                _error!,
                                style: const TextStyle(
                                  color: Colors.red,
                                  fontSize: 12,
                                ),
                              ),
                            ),
                          ]),
                        ),
                      ],

                      const SizedBox(height: 24),

                      // Bouton connexion
                      ElevatedButton(
                        onPressed: _loading
                            ? null
                            : _login,
                        style: ElevatedButton.styleFrom(
                          padding:
                              const EdgeInsets
                              .symmetric(vertical: 14),
                          backgroundColor:
                              const Color(0xFF1565C0),
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(
                            borderRadius:
                                BorderRadius.circular(8),
                          ),
                        ),
                        child: _loading
                            ? const SizedBox(
                                height: 20,
                                width:  20,
                                child:
                                CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ))
                            : const Text(
                                'Se connecter',
                                style: TextStyle(
                                    fontSize: 16),
                              ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _emailCtrl.dispose();
    _passwordCtrl.dispose();
    super.dispose();
  }
}