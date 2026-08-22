import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'loading_screen.dart';

class CameraScreen extends StatefulWidget {
  final String location;
  const CameraScreen({super.key, required this.location});

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {

  File?   _videoFile;
  bool    _isRecording = false;
  final   ImagePicker _picker = ImagePicker();

  Future<void> _recordVideo() async {
    setState(() => _isRecording = true);
    try {
      final XFile? video = await _picker.pickVideo(
        source: ImageSource.camera,
        maxDuration: const Duration(seconds: 30),
      );
      if (video != null) {
        setState(() => _videoFile = File(video.path));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Erreur caméra : $e')),
        );
      }
    } finally {
      setState(() => _isRecording = false);
    }
  }

  Future<void> _pickFromGallery() async {
    try {
      final XFile? video = await _picker.pickVideo(
        source: ImageSource.gallery,
        maxDuration: const Duration(seconds: 60),
      );
      if (video != null) {
        setState(() => _videoFile = File(video.path));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Erreur galerie : $e')),
        );
      }
    }
  }

  void _startAnalysis() {
    if (_videoFile == null) return;
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (_) => LoadingScreen(
          videoFile: _videoFile!,
          location:  widget.location,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Capture — ${widget.location}'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [

            // Zone vidéo
            Expanded(
              child: _videoFile == null
                  ? _buildPlaceholder()
                  : _buildVideoPreview(),
            ),

            const SizedBox(height: 24),

            // Boutons
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _isRecording ? null : _recordVideo,
                    icon: const Icon(Icons.videocam),
                    label: const Text('Filmer'),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(
                          vertical: 14),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _pickFromGallery,
                    icon: const Icon(Icons.video_library),
                    label: const Text('Galerie'),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(
                          vertical: 14),
                    ),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 12),

            ElevatedButton.icon(
              onPressed: _videoFile != null
                  ? _startAnalysis
                  : null,
              icon: const Icon(Icons.analytics),
              label: const Text(
                'Analyser la vidéo',
                style: TextStyle(fontSize: 16),
              ),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPlaceholder() {
    return Container(
      decoration: BoxDecoration(
        color: Colors.grey[100],
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey[300]!),
      ),
      child: const Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.video_call,
              size: 80, color: Colors.grey),
          SizedBox(height: 16),
          Text(
            'Aucune vidéo sélectionnée',
            style: TextStyle(
              color: Colors.grey, fontSize: 16),
          ),
          SizedBox(height: 8),
          Text(
            'Filmez la pièce pendant 5 à 10 secondes',
            style: TextStyle(
              color: Colors.grey, fontSize: 12),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildVideoPreview() {
    final sizeKB = _videoFile!.lengthSync() / 1024;
    final sizeMB = sizeKB / 1024;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.green[50],
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.green[300]!),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.check_circle,
              size: 64, color: Colors.green),
          const SizedBox(height: 16),
          const Text(
            'Vidéo sélectionnée',
            style: TextStyle(
              color: Colors.green,
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            _videoFile!.path.split('\\').last,
            style: const TextStyle(
              color: Colors.grey, fontSize: 12),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 4),
          Text(
            '${sizeMB.toStringAsFixed(1)} MB',
            style: const TextStyle(
              color: Colors.grey, fontSize: 12),
          ),
          const SizedBox(height: 16),
          TextButton.icon(
            onPressed: _recordVideo,
            icon: const Icon(Icons.refresh),
            label: const Text('Changer de vidéo'),
          ),
        ],
      ),
    );
  }
}