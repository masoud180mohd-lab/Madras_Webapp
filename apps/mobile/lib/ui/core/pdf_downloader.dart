import 'dart:io';
import 'package:flutter/material.dart';
import 'package:open_filex/open_filex.dart';
import 'package:path_provider/path_provider.dart';

class PdfDownloader {
  /// Saves PDF bytes locally and immediately attempts to open the file with
  /// the system's default PDF viewer / application.
  static Future<void> saveAndOpen(
    BuildContext context, {
    required List<int> bytes,
    required String filename,
    String? successMessage,
  }) async {
    try {
      final dir = await getApplicationDocumentsDirectory();
      final safeName = filename.replaceAll(RegExp(r'[^\w.\-]+'), '_');
      final file = File('${dir.path}/$safeName');
      await file.writeAsBytes(bytes, flush: true);

      if (!context.mounted) return;

      final result = await OpenFilex.open(file.path);
      if (!context.mounted) return;

      if (result.type != ResultType.done) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(successMessage ?? 'Faili imehifadhiwa: ${file.path}'),
            duration: const Duration(seconds: 4),
          ),
        );
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Imeshindikana kuhifadhi PDF: $e'),
            backgroundColor: Colors.red.shade700,
          ),
        );
      }
    }
  }
}
