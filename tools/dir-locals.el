;;; Directory Local Variables
;;; For more information see (info "(emacs) Directory Variables")

((python-mode . ((eval . (with-eval-after-load 'flycheck
                           (flycheck-define-checker python-ty
                                                    "A Python type checker using ty."
                                                    :command ("ty" "check"
                                                              "--color=never"
                                                              "--output-format=concise"
                                                              source-original)
                                                    :working-directory flycheck-python-find-project-root
                                                    :error-patterns
                                                    ((error line-start
                                                            (file-name) ":" line ":" column ": error"
                                                            (optional "[" (id (one-or-more (not (any "]")))) "]")
                                                            " " (message) line-end)
                                                     (warning line-start
                                                              (file-name) ":" line ":" column ": warning"
                                                              (optional "[" (id (one-or-more (not (any "]")))) "]")
                                                              " " (message) line-end)
                                                     (info line-start
                                                           (file-name) ":" line ":" column ": info"
                                                           (optional "[" (id (one-or-more (not (any "]")))) "]")
                                                           " " (message) line-end))
                                                    :predicate flycheck-buffer-saved-p
                                                    :modes (python-mode python-ts-mode))
                           (flycheck-add-next-checker 'python-ruff '(t . python-ty))))
                 (mode . flycheck)
                 (mode . company)
                 (flycheck-checker . python-ruff)
                 (flycheck-disabled-checkers . (python-mypy python-flake8
                                                            python-pylint)))))
