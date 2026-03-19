# ML_explained

A collection of Jupyter notebooks covering the mathematical foundations of Machine Learning and Statistics — written for engineers who use ML in practice and want to understand *why* the methods work, not just *that* they work.

Each notebook follows the same structure: **intuition first → key formula → proof sketch or derivation → plots generated from code**.

---

## Who this is for

You use `sklearn`, `xgboost`, or `torch` regularly. You know how to fit a model and evaluate it. But when someone asks *"why do we use cross-entropy loss?"* or *"what does the Hessian have to do with convexity?"* — you want a precise answer, not a hand-wave.

These notebooks sit between a blog post and a textbook. No proofs for their own sake, but no magic either.

---

## Structure

```
ml-math-sheets/
│
├── 00_glossary.ipynb                  ← Start here
├── 00b_statistical_indicators.ipynb
├── 00c_ml_metrics.ipynb
│
├── 01_gradient_descent.ipynb
├── 02_linear_regression.ipynb
├── 03_logistic_regression.ipynb
├── 04_neural_networks_backprop.ipynb
├── 05_decision_trees.ipynb
├── 06_xgboost.ipynb
├── 07_kmeans.ipynb
└── 08_gmm_em.ipynb
```

---

## Notebooks

### Foundations

| Notebook | Topics | Key formulas |
|----------|--------|--------------|
| [`00_glossary`](./00_glossary.ipynb) | Vectors, matrices, dot product, eigenvectors, derivatives, chain rule, gradient, Gaussian, covariance, Bayes, convexity, L1/L2 norms | $Av = \lambda v$ · $\nabla f$ · $\mathcal{N}(\mu, \sigma^2)$ · $P(A\|B) \propto P(B\|A)P(A)$ |
| [`00b_statistical_indicators`](./00b_statistical_indicators.ipynb) | Mean, variance, correlation, z-score, CLT, confidence intervals, t-test, p-value | $s^2 = \frac{1}{n-1}\sum(x_i-\bar{x})^2$ · $\text{SE} = \sigma/\sqrt{n}$ · $t = (\bar{x}-\mu_0)/(s/\sqrt{n})$ |
| [`00c_ml_metrics`](./00c_ml_metrics.ipynb) | MSE, RMSE, MAE, R², confusion matrix, precision, recall, F1, ROC/AUC, log-loss | $R^2 = 1 - SS_{res}/SS_{tot}$ · $F_1 = 2PR/(P+R)$ · $\text{AUC} = P(\hat{p}_{+} > \hat{p}_{-})$ |

### Optimisation

| Notebook | Topics | Key formulas |
|----------|--------|--------------|
| [`01_gradient_descent`](./01_gradient_descent.ipynb) | Update rule, convexity, Hessian, BGD/SGD/mini-batch, learning rate, Momentum, RMSProp, Adam, saddle points, vanishing gradients | $\theta \leftarrow \theta - \eta\nabla_\theta\mathcal{L}$ · Adam bias correction |

### Supervised Learning

| Notebook | Topics | Key formulas |
|----------|--------|--------------|
| [`02_linear_regression`](./02_linear_regression.ipynb) | MSE, Normal equation, OLS geometry, Gauss-Markov, Ridge, Lasso, R², bias-variance tradeoff | $\hat{\theta} = (X^\top X)^{-1}X^\top y$ · $\hat{\theta}_{\text{ridge}} = (X^\top X + \lambda I)^{-1}X^\top y$ |
| [`03_logistic_regression`](./03_logistic_regression.ipynb) | Sigmoid, log-odds, decision boundary, BCE loss, MLE, gradient derivation, Softmax, regularisation | $\hat{p} = \sigma(x^\top\theta)$ · $\nabla_\theta\mathcal{L} = \frac{1}{n}X^\top(\hat{p}-y)$ · Softmax |
| `04_neural_networks_backprop` | Forward pass, activation functions, backpropagation, chain rule in depth, initialisation | $\frac{\partial\mathcal{L}}{\partial W^{(l)}} = \delta^{(l)}(a^{(l-1)})^\top$ |
| `05_decision_trees` | Gini impurity, entropy, information gain, splitting criterion, pruning | $H = -\sum_c p_c \log p_c$ · $\text{IG} = H(\text{parent}) - \sum_k \frac{n_k}{n}H(k)$ |
| `06_xgboost` | Boosting, additive trees, gradient boosting, Taylor expansion of loss, regularised objective | $\mathcal{L}^{(t)} \approx \sum_i [g_i f_t(x_i) + \frac{1}{2}h_i f_t^2(x_i)] + \Omega(f_t)$ |

### Unsupervised Learning

| Notebook | Topics | Key formulas |
|----------|--------|--------------|
| `07_kmeans` | Objective function, Lloyd's algorithm, convergence, initialisation (k-means++), limitations | $\mathcal{L} = \sum_{k}\sum_{i \in C_k}\|x_i - \mu_k\|^2$ |
| `08_gmm_em` | Gaussian mixture model, EM algorithm, E-step, M-step, log-likelihood, BIC | $p(x) = \sum_k \pi_k \mathcal{N}(x;\mu_k,\Sigma_k)$ |

---

## Mathematical prerequisites

These notebooks assume you are comfortable with:
- High-school calculus (derivatives, chain rule)
- Basic linear algebra (matrix multiply, transpose)
- Some probability (expectation, variance, conditional probability)

Everything beyond that is built up from scratch in [`00_glossary.ipynb`](./00_glossary.ipynb).

---

## Core ideas that connect everything

Understanding these five ideas will make every notebook click faster.

**1. A model is a function of parameters**

Every ML model is a function $f_\theta: \mathbb{R}^p \to \mathbb{R}$ (or $\mathbb{R}^C$). Training means finding the $\theta$ that makes $f_\theta$ match the data. All the complexity is in *how* you define "match" and *how* you search for $\theta$.

**2. A loss function is a compass**

The loss $\mathcal{L}(\theta)$ tells you how wrong the current $\theta$ is. Training is optimisation: find $\theta^* = \arg\min_\theta \mathcal{L}(\theta)$. The choice of loss is not cosmetic — it encodes your probabilistic assumptions about the data-generating process (MSE → Gaussian noise, BCE → Bernoulli, categorical CE → Multinomial).

**3. Convexity is the guarantee you want**

If $\mathcal{L}$ is convex, gradient descent finds the global minimum. If it is not (neural networks), you rely on good initialisation, careful architecture, and empirical evidence that local minima generalise well. Knowing whether your loss is convex changes how much you trust your training procedure.

**4. The gradient is a map of the loss landscape**

$\nabla_\theta \mathcal{L} \in \mathbb{R}^{|\theta|}$ lives in parameter space — it has the same dimension as the number of model parameters, not the number of features. It points toward steepest ascent. Every gradient descent variant (SGD, Adam, Adagrad) is just a different strategy for following $-\nabla_\theta\mathcal{L}$.

**5. MLE connects loss functions to probability**

Minimising a loss is almost always equivalent to maximising a likelihood under some assumed data distribution. Ridge = MLE with Gaussian prior on weights (MAP). Lasso = MLE with Laplace prior. This probabilistic view explains why the formulas are what they are and guides you when you need to design a custom loss.

---

## How the notebooks are connected

```
00_glossary  ──────────────────────────────────────────────┐
00b_statistical_indicators ────────────────────────────────┤
00c_ml_metrics ─────────────────────────────────────────── foundations
                                                            │
01_gradient_descent ───────────────────────────────────────┤
        │                                                   │
        ├── 02_linear_regression ──┐                        │
        │         │                │                        │
        │         └── 03_logistic  │                        │
        │                  │       │                        │
        │                  └── 04_neural_networks           │
        │                                                   │
        ├── 05_decision_trees ── 06_xgboost                 │
        │                                                   │
        └── 07_kmeans ── 08_gmm_em ─────────────────────────┘
```

Gradient descent is the spine of the supervised learning notebooks — every model in 02–04 is trained by following a gradient. Trees and XGBoost break that pattern intentionally (no gradient on the tree structure itself), which is part of what makes them powerful on tabular data.

---

## Running the notebooks

```bash
git clone https://github.com/TGM-hub/ml-math-sheets
cd ml-math-sheets
pip install numpy matplotlib scipy scikit-learn
jupyter notebook
```

Each notebook saves its plots to `img/` automatically. Make sure the directory exists (the first code cell handles this with `os.makedirs('img', exist_ok=True)`).

---

## Notation reference

| Symbol | Meaning |
|--------|---------|
| $n$ | Number of samples |
| $p$ | Number of features |
| $X \in \mathbb{R}^{n \times p}$ | Design matrix (rows = samples) |
| $y \in \mathbb{R}^n$ | Target vector |
| $\theta \in \mathbb{R}^{p+1}$ | Model parameters (includes bias) |
| $\hat{y}$, $\hat{p}$ | Predicted values / probabilities |
| $\mathcal{L}(\theta)$ | Loss function |
| $\nabla_\theta \mathcal{L}$ | Gradient of loss w.r.t. $\theta$ |
| $\eta$ | Learning rate |
| $\sigma(z)$ | Sigmoid: $1/(1+e^{-z})$ |
| $\lambda$ | Regularisation strength |
| $H$ | Hessian matrix $\nabla^2 \mathcal{L}$ |
| $\mathbb{E}[X]$ | Expectation of $X$ |
| $\text{Var}(X)$ | Variance of $X$ |
| $\mathcal{N}(\mu, \sigma^2)$ | Gaussian distribution |

---

*Part of [TGM-hub](https://github.com/TGM-hub) · Built to understand ML from the inside out*

