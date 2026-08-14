import 'package:flutter/material.dart';

import '../../../core/copy.dart';
import '../../../core/theme.dart';
import '../view_models/auth_view_model.dart';

class LoginView extends StatefulWidget {
  const LoginView({super.key, required this.viewModel});

  final AuthViewModel viewModel;

  @override
  State<LoginView> createState() => _LoginViewState();
}

class _LoginViewState extends State<LoginView> {
  final _username = TextEditingController();
  final _password = TextEditingController();
  String? _localError;

  @override
  void dispose() {
    _username.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final username = _username.text.trim();
    final password = _password.text;
    if (username.isEmpty) {
      setState(() => _localError = MadrasaCopy.needUsername);
      return;
    }
    if (password.isEmpty) {
      setState(() => _localError = MadrasaCopy.needPassword);
      return;
    }
    setState(() => _localError = null);
    await widget.viewModel.login(username: username, password: password);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: ListenableBuilder(
          listenable: widget.viewModel,
          builder: (context, _) {
            final error = _localError ?? widget.viewModel.error;
            return Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 420),
                child: SingleChildScrollView(
                  padding: const EdgeInsets.fromLTRB(24, 32, 24, 24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        MadrasaCopy.brand,
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          fontFamily: 'serif',
                          fontSize: 22,
                          fontWeight: FontWeight.w700,
                          color: MadrasaTheme.forest,
                        ),
                      ),
                      const SizedBox(height: 8),
                      const Divider(color: MadrasaTheme.gold, thickness: 2),
                      const SizedBox(height: 16),
                      Text(
                        MadrasaCopy.welcome,
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.headlineMedium
                            ?.copyWith(
                              color: MadrasaTheme.ink,
                              fontWeight: FontWeight.w700,
                            ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        MadrasaCopy.subtitle,
                        textAlign: TextAlign.center,
                        style: const TextStyle(color: MadrasaTheme.muted),
                      ),
                      const SizedBox(height: 28),
                      TextField(
                        key: const Key('login_username'),
                        controller: _username,
                        textInputAction: TextInputAction.next,
                        autofillHints: const [AutofillHints.username],
                        decoration: const InputDecoration(
                          labelText: MadrasaCopy.username,
                        ),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        key: const Key('login_password'),
                        controller: _password,
                        obscureText: true,
                        onSubmitted: (_) => _submit(),
                        autofillHints: const [AutofillHints.password],
                        decoration: const InputDecoration(
                          labelText: MadrasaCopy.password,
                        ),
                      ),
                      if (error != null) ...[
                        const SizedBox(height: 12),
                        Text(
                          error,
                          style: const TextStyle(color: MadrasaTheme.danger),
                        ),
                      ],
                      const SizedBox(height: 20),
                      FilledButton(
                        key: const Key('login_submit'),
                        onPressed: widget.viewModel.busy ? null : _submit,
                        child: widget.viewModel.busy
                            ? const SizedBox(
                                height: 22,
                                width: 22,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                            : const Text(MadrasaCopy.login),
                      ),
                    ],
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}
