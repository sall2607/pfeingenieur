import 'package:flutter/material.dart';
import '../models/equipment.dart';

class EditScreen extends StatefulWidget {
  final Equipment equipment;
  const EditScreen({super.key, required this.equipment});

  @override
  State<EditScreen> createState() => _EditScreenState();
}

class _EditScreenState extends State<EditScreen> {

  late TextEditingController _nameCtrl;
  late TextEditingController _brandCtrl;
  late TextEditingController _modelCtrl;
  late TextEditingController _serialCtrl;
  late TextEditingController _powerCtrl;
  late TextEditingController _voltageCtrl;
  late TextEditingController _tempCtrl;
  late TextEditingController _coolingCtrl;

  late String _designation;
  late String _status;

  // Libellés lisibles pour les statuts
  static const Map<String, String> _statusLabels = {
    'Toujours_en_marche':
        'Toujours en marche',
    'En_marche_pendant_les_horaires_de_travail':
        'En marche (horaires de travail)',
    'En_marche_selon_un_planning_specifique':
        'En marche (planning spécifique)',
    'En_marche_selon_un_besoin':
        'En marche selon un besoin',
    'Mode_saisonnier':
        'Mode saisonnier',
    'Mode_maintenance':
        'Mode maintenance',
    'NonDetachable':
        'Non détachable',
    'Inactif':
        'Inactif',
  };

  // Libellés lisibles pour les désignations
  static const Map<String, String> _designationLabels = {
    'AppareilCuisine':          '🍳 Appareil cuisine',
    'AppareilInformatique':     '💻 Appareil informatique',
    'Climatisation':            '❄️  Climatisation',
    'Eclairage':                '💡 Éclairage',
    'Robinet':                  '🚿 Robinet',
    'Refrigeration':            '🧊 Réfrigération',
    'PeripheriqueImpression':   '🖨️  Périphérique impression',
    'InfrastructureIT':         '🌐 Infrastructure IT',
    'Autres':                   '📦 Autres',
  };

  @override
  void initState() {
    super.initState();
    final e = widget.equipment;
    _nameCtrl    = TextEditingController(text: e.name);
    _brandCtrl   = TextEditingController(text: e.brand ?? '');
    _modelCtrl   = TextEditingController(text: e.model ?? '');
    _serialCtrl  = TextEditingController(
        text: e.serialNumber ?? '');
    _powerCtrl   = TextEditingController(
        text: e.power?.toString() ?? '');
    _voltageCtrl = TextEditingController(
        text: e.voltage?.toString() ?? '');
    _tempCtrl    = TextEditingController(
        text: e.temperature?.toString() ?? '');
    _coolingCtrl = TextEditingController(
        text: e.coolingCapacity?.toString() ?? '');
    _designation = e.designation;
    _status      = e.equipmentStatus;
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _brandCtrl.dispose();
    _modelCtrl.dispose();
    _serialCtrl.dispose();
    _powerCtrl.dispose();
    _voltageCtrl.dispose();
    _tempCtrl.dispose();
    _coolingCtrl.dispose();
    super.dispose();
  }

  void _save() {
    if (_nameCtrl.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Le nom est obligatoire'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    final updated = Equipment(
      id:              widget.equipment.id,
      name:            _nameCtrl.text.trim(),
      designation:     _designation,
      equipmentStatus: _status,
      brand:           _brandCtrl.text.trim().isEmpty
                           ? null
                           : _brandCtrl.text.trim(),
      model:           _modelCtrl.text.trim().isEmpty
                           ? null
                           : _modelCtrl.text.trim(),
      serialNumber:    _serialCtrl.text.trim().isEmpty
                           ? null
                           : _serialCtrl.text.trim(),
      power:           int.tryParse(_powerCtrl.text.trim()),
      voltage:         int.tryParse(_voltageCtrl.text.trim()),
      temperature:     double.tryParse(_tempCtrl.text.trim()),
      coolingCapacity: int.tryParse(
                           _coolingCtrl.text.trim()),
      location:        widget.equipment.location,
      confidence:      widget.equipment.confidence,
      needsReview:     false,
      detectedAt:      widget.equipment.detectedAt,
    );
    Navigator.pop(context, updated);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Corriger la fiche'),
        actions: [
          TextButton.icon(
            onPressed: _save,
            icon: const Icon(
                Icons.save, color: Colors.white),
            label: const Text('Enregistrer',
                style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [

            // Bandeau needsReview
            Container(
              padding: const EdgeInsets.all(12),
              margin: const EdgeInsets.only(bottom: 20),
              decoration: BoxDecoration(
                color: Colors.orange[50],
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                    color: Colors.orange.shade300),
              ),
              child: const Row(
                children: [
                  Icon(Icons.warning_amber,
                      color: Colors.orange, size: 20),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Cette fiche nécessite une vérification. '
                      'Complétez ou corrigez les champs ci-dessous.',
                      style: TextStyle(
                          fontSize: 13,
                          color: Colors.orange),
                    ),
                  ),
                ],
              ),
            ),

            // ── Champs obligatoires ───────────────────
            _sectionTitle('Informations principales'),

            _textField(
              label:      'Nom de l\'équipement *',
              controller: _nameCtrl,
              icon:       Icons.inventory_2,
            ),
            const SizedBox(height: 12),

            _dropdownField(
              label:   'Désignation *',
              value:   _designation,
              items:   _designationLabels,
              icon:    Icons.category,
              onChanged: (v) =>
                  setState(() => _designation = v!),
            ),
            const SizedBox(height: 12),

            _dropdownField(
              label:   'Statut de fonctionnement *',
              value:   _status,
              items:   _statusLabels,
              icon:    Icons.power_settings_new,
              onChanged: (v) =>
                  setState(() => _status = v!),
            ),

            const SizedBox(height: 20),

            // ── Identification ────────────────────────
            _sectionTitle('Identification'),

            _textField(
              label:      'Marque',
              controller: _brandCtrl,
              icon:       Icons.business,
              hint:       'Ex: Daikin, Dell, Cisco...',
            ),
            const SizedBox(height: 12),

            _textField(
              label:      'Modèle',
              controller: _modelCtrl,
              icon:       Icons.label,
              hint:       'Ex: Latitude 5420...',
            ),
            const SizedBox(height: 12),

            _textField(
              label:      'Numéro de série',
              controller: _serialCtrl,
              icon:       Icons.qr_code,
              hint:       'Ex: SN-XXXX-YYYY...',
            ),

            const SizedBox(height: 20),

            // ── Spécifications électriques ────────────
            _sectionTitle('Spécifications électriques'),

            Row(children: [
              Expanded(child: _textField(
                label:      'Puissance (W)',
                controller: _powerCtrl,
                icon:       Icons.bolt,
                isNumber:   true,
                hint:       'Ex: 65',
              )),
              const SizedBox(width: 12),
              Expanded(child: _textField(
                label:      'Tension (V)',
                controller: _voltageCtrl,
                icon:       Icons.electrical_services,
                isNumber:   true,
                hint:       'Ex: 220',
              )),
            ]),

            // ── Champs Climatisation ──────────────────
            if (_designation == 'Climatisation') ...[
              const SizedBox(height: 20),
              _sectionTitle('Paramètres climatisation'),

              Row(children: [
                Expanded(child: _textField(
                  label:      'Température (°C)',
                  controller: _tempCtrl,
                  icon:       Icons.thermostat,
                  isNumber:   true,
                  hint:       'Ex: 22',
                  isDecimal:  true,
                )),
                const SizedBox(width: 12),
                Expanded(child: _textField(
                  label:      'Capacité (BTU)',
                  controller: _coolingCtrl,
                  icon:       Icons.ac_unit,
                  isNumber:   true,
                  hint:       'Ex: 9000',
                )),
              ]),
            ],

            const SizedBox(height: 32),

            // ── Bouton enregistrer ────────────────────
            ElevatedButton.icon(
              onPressed: _save,
              icon: const Icon(Icons.check_circle,
                  size: 20),
              label: const Text(
                'Enregistrer la correction',
                style: TextStyle(fontSize: 16),
              ),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(
                    vertical: 16),
                backgroundColor:
                    const Color(0xFF1565C0),
                foregroundColor: Colors.white,
              ),
            ),

            const SizedBox(height: 16),

            // ── Bouton annuler ────────────────────────
            OutlinedButton.icon(
              onPressed: () =>
                  Navigator.pop(context, null),
              icon: const Icon(Icons.cancel),
              label: const Text('Annuler'),
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.symmetric(
                    vertical: 14),
              ),
            ),

            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  // ── Widgets utilitaires ─────────────────────────

  Widget _sectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          Container(
            width: 4, height: 18,
            decoration: BoxDecoration(
              color: const Color(0xFF1565C0),
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(width: 8),
          Text(
            title,
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.bold,
              color: Color(0xFF1565C0),
            ),
          ),
        ],
      ),
    );
  }

  Widget _textField({
    required String label,
    required TextEditingController controller,
    required IconData icon,
    String? hint,
    bool isNumber  = false,
    bool isDecimal = false,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label,
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w500,
              color: Colors.black87,
            )),
        const SizedBox(height: 6),
        TextFormField(
          controller:   controller,
          keyboardType: isDecimal
              ? const TextInputType.numberWithOptions(
                  decimal: true)
              : isNumber
                  ? TextInputType.number
                  : TextInputType.text,
          decoration: InputDecoration(
            hintText:        hint,
            prefixIcon:      Icon(icon, size: 18),
            border:          OutlineInputBorder(
                borderRadius: BorderRadius.circular(8)),
            filled:          true,
            fillColor:       Colors.grey[50],
            contentPadding:  const EdgeInsets.symmetric(
                horizontal: 12, vertical: 10),
            hintStyle: const TextStyle(
                color: Colors.grey, fontSize: 13),
          ),
        ),
      ],
    );
  }

  Widget _dropdownField({
    required String label,
    required String value,
    required Map<String, String> items,
    required IconData icon,
    required void Function(String?) onChanged,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label,
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w500,
              color: Colors.black87,
            )),
        const SizedBox(height: 6),
        DropdownButtonFormField<String>(
          value:       value,
          isExpanded:  true,
          decoration:  InputDecoration(
            prefixIcon: Icon(icon, size: 18),
            border:     OutlineInputBorder(
                borderRadius: BorderRadius.circular(8)),
            filled:     true,
            fillColor:  Colors.grey[50],
            contentPadding: const EdgeInsets.symmetric(
                horizontal: 12, vertical: 10),
          ),
          items: items.entries.map((entry) =>
            DropdownMenuItem(
              value: entry.key,
              child: Text(
                entry.value,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontSize: 13),
              ),
            )
          ).toList(),
          onChanged: onChanged,
        ),
      ],
    );
  }
}