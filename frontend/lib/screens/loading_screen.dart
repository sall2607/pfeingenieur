import 'dart:io';
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/equipment.dart';
import 'results_screen.dart';
import '../services/auth_service.dart';

class LoadingScreen extends StatefulWidget {
  final File   videoFile;
  final String location;

  const LoadingScreen({
    super.key,
    required this.videoFile,
    required this.location,
  });

  @override
  State<LoadingScreen> createState() => _LoadingScreenState();
}

class _LoadingScreenState extends State<LoadingScreen>
    with TickerProviderStateMixin {

  late AnimationController _animController;
  String _currentStep = 'Envoi de la vidéo...';
  int    _stepIndex   = 0;

  final List<String> _steps = [
    'Envoi de la vidéo...',
    'Extraction des keyframes...',
    'Détection YOLO-World...',
    'Déduplication ByteTrack...',
    'Recherche RAG Qdrant...',
    'Analyse Gemini 2.5 Flash...',
    'Validation des fiches...',
    'Finalisation...',
  ];

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat();

    _startAnalysis();
    _animateSteps();
  }

  void _animateSteps() {
    Future.doWhile(() async {
      await Future.delayed(const Duration(seconds: 4));
      if (!mounted) return false;
      if (_stepIndex < _steps.length - 1) {
        setState(() {
          _stepIndex++;
          _currentStep = _steps[_stepIndex];
        });
        return true;
      }
      return false;
    });
  }

  Future<void> _startAnalysis() async {
    // Récupérer l'userId
    final userId = await AuthService.getUserId();

    final result = await ApiService.analyzeVideo(
      videoFile: widget.videoFile,
      location:  widget.location,
      userId:       userId,        // ← AJOUTER
    );

    if (!mounted) return;

    if (result['success'] == true) {
      final equipments =
          result['equipments'] as List<Equipment>;
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (_) => ResultsScreen(
            equipments:     equipments,
            location:       widget.location,
            processingTime: result['data']
                ['processing_time'] ?? 0.0,
            metadata: result['data']['metadata'] ?? {},
          ),
        ),
      );
    } else {
      Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
              'Erreur : ${result['error']}'),
          backgroundColor: Colors.red,
          duration: const Duration(seconds: 5),
        ),
      );

    // Message spécifique si quota dépassé
    final errorMsg = result['error'] ?? 'Erreur inconnue';
    final isQuota  = errorMsg.contains('Quota') ||
                     errorMsg.contains('429');
    
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(isQuota
            ? '⚠️ Quota journalier atteint (3 analyses/jour)'
            : 'Erreur : $errorMsg'),
        backgroundColor: isQuota
            ? Colors.orange
            : Colors.red,
        duration: const Duration(seconds: 5),
      ),
    );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF1565C0),
      body: SafeArea(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [

                // Logo
                const Icon(Icons.auto_awesome,
                    size: 64, color: Colors.white),
                const SizedBox(height: 24),

                const Text(
                  'Analyse en cours...',
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),

                const SizedBox(height: 8),
                Text(
                  widget.location,
                  style: const TextStyle(
                    fontSize: 14,
                    color: Colors.white70,
                  ),
                ),

                const SizedBox(height: 48),

                // Spinner
                RotationTransition(
                  turns: _animController,
                  child: Container(
                    width: 80, height: 80,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(
                          color: Colors.white, width: 3),
                    ),
                    child: const Icon(
                      Icons.psychology,
                      size: 40,
                      color: Colors.white,
                    ),
                  ),
                ),

                const SizedBox(height: 48),

                // Étape courante
                AnimatedSwitcher(
                  duration: const Duration(milliseconds: 300),
                  child: Text(
                    _currentStep,
                    key: ValueKey(_currentStep),
                    style: const TextStyle(
                      fontSize: 16,
                      color: Colors.white,
                      fontWeight: FontWeight.w500,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ),

                const SizedBox(height: 16),

                // Barre de progression
                LinearProgressIndicator(
                  value: (_stepIndex + 1) / _steps.length,
                  backgroundColor: Colors.white24,
                  valueColor: const AlwaysStoppedAnimation(
                      Colors.white),
                ),

                const SizedBox(height: 8),
                Text(
                  'Étape ${_stepIndex + 1} / ${_steps.length}',
                  style: const TextStyle(
                    fontSize: 12,
                    color: Colors.white60,
                  ),
                ),

                const SizedBox(height: 48),
                const Text(
                  'Ne fermez pas l\'application\n'
                  'pendant l\'analyse.',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.white54,
                  ),
                  textAlign: TextAlign.center,
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
    _animController.dispose();
    super.dispose();
  }
}