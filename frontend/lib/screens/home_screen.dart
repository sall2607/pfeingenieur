import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'camera_screen.dart';
import 'dashboard_screen.dart';
import '../services/auth_service.dart';
import 'login_screen.dart';


class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {

  final TextEditingController _locationController =
      TextEditingController(text: 'Bureau standard');
  bool _serverOk  = false;
  bool _checking  = true;
  String _selectedLocation = 'Bureau standard'; // ← AJOUTER

  // Localisations prédéfinies SFM
  final List<String> _locations = [
    'Bureau standard',
    'Salle technique',
    'Salle de réunion',
    'Cuisine',
    'Couloir',
    'Entrepôt',
    'Datacenter',
    'Accueil',
  ];

  // Dans initState
String? _userId;
int _quotaRemaining = 3;

  @override
  void initState() {
    super.initState();
    _checkServer();
    
  }

 Future<void> _initUser() async {
  final user = await AuthService.getUser();
  if (user != null) {
    setState(() => _userId = user['id']);

    try {
      final quota = await ApiService.getQuota(
          user['id']);
      setState(() {
        _quotaRemaining =
            (quota['remaining'] as num?)
            ?.toInt() ?? 3;
      });
      
    } catch (e) {
      // En cas d'erreur, afficher 3 par défaut
      setState(() => _quotaRemaining = 3);
    }
  }
}

  Future<void> _checkServer() async {
    setState(() => _checking = true);
    final ok = await ApiService.healthCheck();
    setState(() {
      _serverOk = ok;
      _checking = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('SFM Equipment Detection'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _checkServer,
            tooltip: 'Vérifier le serveur',
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: _logout,
            tooltip: 'Se déconnecter',
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [

            // Logo / Header
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: const Color(0xFF1565C0),
                borderRadius: BorderRadius.circular(16),
              ),
              child: const Column(
                children: [
                  Icon(Icons.business,
                      size: 60, color: Colors.white),
                  SizedBox(height: 12),
                  Text(
                    'SFM Technologies',
                    style: TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  SizedBox(height: 4),
                  Text(
                    'Détection automatique d\'équipements',
                    style: TextStyle(
                      fontSize: 13,
                      color: Colors.white70,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),

            const SizedBox(height: 28),

            // Statut serveur
            _buildServerStatus(),

            // Ajouter dans le build, après le statut serveur :
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: _quotaRemaining > 0
                    ? Colors.green[50]
                    : Colors.red[50],
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                  color: _quotaRemaining > 0
                      ? Colors.green.shade300
                      : Colors.red.shade300,
                ),
              ),
              child: Row(children: [
                Icon(
                  _quotaRemaining > 0
                      ? Icons.video_library
                      : Icons.block,
                  color: _quotaRemaining > 0
                      ? Colors.green
                      : Colors.red,
                  size: 18,
                ),
                const SizedBox(width: 8),
                Text(
                  _quotaRemaining > 0
                      ? 'Analyses restantes aujourd\'hui : '
                        '$_quotaRemaining / 3'
                      : 'Quota journalier atteint — '
                        'réessayez demain',
                  style: TextStyle(
                    color: _quotaRemaining > 0
                        ? Colors.green[800]
                        : Colors.red[800],
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ]),
            ),

            
            const SizedBox(height: 24),

            // Sélection localisation
            Text(
              'Localisation du site',
              style: Theme.of(context).textTheme.titleMedium
                  ?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),

            // Dropdown localisations
            // Remplacer tout le DropdownButtonFormField par :
            DropdownButtonFormField<String>(
              value: _selectedLocation,   // ← variable séparée
              decoration: InputDecoration(
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                prefixIcon: const Icon(Icons.location_on),
                filled: true,
                fillColor: Colors.grey[50],
              ),
              items: _locations.map((loc) =>
                DropdownMenuItem(value: loc, child: Text(loc))
              ).toList(),
              onChanged: (val) {
                if (val != null) {
                  setState(() {
                    _selectedLocation = val;
                    _locationController.text = val;
                  });
                }
              },
            ),

            /*const SizedBox(height: 8),

            // Ou saisie manuelle
            TextFormField(
              controller: _locationController,
              decoration: InputDecoration(
                hintText: 'Ou saisir une localisation...',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                prefixIcon: const Icon(Icons.edit_location),
                filled: true,
                //fillColor: Colors.grey[50],
              //),
            ),*/

            const SizedBox(height: 32),

            // Bouton analyser
            ElevatedButton.icon(
              onPressed: (_serverOk && !_checking)
                  ? _startAnalysis
                  : null,
              icon: const Icon(Icons.videocam, size: 24),
              label: const Text(
                'Démarrer l\'analyse',
                style: TextStyle(fontSize: 16),
              ),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
            ),

            const SizedBox(height: 12),
            OutlinedButton.icon(
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => const DashboardScreen(),
              ),
            ),
            icon: const Icon(Icons.dashboard),
            label: const Text('Tableau de bord'),
            style: OutlinedButton.styleFrom(
              padding: const EdgeInsets.symmetric(
                  vertical: 14),
            ),
          ),


            const SizedBox(height: 16),

            // Info
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.blue[50],
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.blue[200]!),
              ),
              child: const Row(
                children: [
                  Icon(Icons.info_outline,
                      color: Colors.blue, size: 18),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Filmez la pièce pendant 5 à 10 secondes '
                      'en passant devant chaque équipement.',
                      style: TextStyle(
                        fontSize: 12, color: Colors.blue),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildServerStatus() {
    Color color;
    IconData icon;
    String message;

    if (_checking) {
      color   = Colors.orange;
      icon    = Icons.sync;
      message = 'Vérification du serveur...';
    } else if (_serverOk) {
      color   = Colors.green;
      icon    = Icons.check_circle;
      message = 'Serveur connecté — ${ApiService.serverUrl}';
    } else {
      color   = Colors.red;
      icon    = Icons.error;
      message = 'Serveur inaccessible — ${ApiService.serverUrl}';
    }

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          _checking
              ? SizedBox(
                  width: 18, height: 18,
                  child: CircularProgressIndicator(
                    strokeWidth: 2, color: color))
              : Icon(icon, color: color, size: 18),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              message,
              style: TextStyle(
                color: color,
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }
  
  

  void _startAnalysis() async {
    final location = _locationController.text.trim();
    if (location.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Veuillez saisir une localisation'),
        ),
      );
      return;
    }
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => CameraScreen(location: location),
      ),
    );

    // ← AJOUTER : rafraîchir quota au retour
    await _initUser();
  }

  @override
  void dispose() {
    _locationController.dispose();
    super.dispose();
  }

    // Méthode logout
  Future<void> _logout() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Déconnexion'),
        content: const Text(
            'Voulez-vous vous déconnecter ?'),
        actions: [
          TextButton(
            onPressed: () =>
                Navigator.pop(ctx, false),
            child: const Text('Annuler'),
          ),
          ElevatedButton(
            onPressed: () =>
                Navigator.pop(ctx, true),
            style: ElevatedButton.styleFrom(
              backgroundColor:
                  const Color(0xFF1565C0),
              foregroundColor: Colors.white,
            ),
            child: const Text('Déconnecter'),
          ),
        ],
      ),
    );

    if (confirm == true) {
      await AuthService.logout();
      if (mounted) {
        Navigator.pushAndRemoveUntil(
          context,
          MaterialPageRoute(
              builder: (_) => const LoginScreen()),
          (r) => false,
        );
      }
    }
  }
}