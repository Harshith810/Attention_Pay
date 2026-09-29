import torch
import torch.nn as nn


class TabTransformer(nn.Module):

    def __init__(
        self,
        cat_cardinalities,
        num_numerical,
        embed_dim,
        n_heads,
        n_layers,
        num_classes,
        dropout
    ):

        super().__init__()

        # ----------------------------------------------------
        # Categorical embeddings
        # ----------------------------------------------------

        self.cat_embeddings = nn.ModuleList([

            nn.Embedding(
                cardinality,
                embed_dim
            )

            for cardinality
            in cat_cardinalities

        ])

        # ----------------------------------------------------
        # Transformer encoder
        # ----------------------------------------------------

        encoder_layer = nn.TransformerEncoderLayer(

            d_model=embed_dim,

            nhead=n_heads,

            dim_feedforward=embed_dim * 4,

            dropout=dropout,

            activation="gelu",

            batch_first=True,

            norm_first=False

        )

        self.transformer = nn.TransformerEncoder(

            encoder_layer,

            num_layers=n_layers

        )

        # ----------------------------------------------------
        # Numerical feature normalization
        # ----------------------------------------------------

        self.num_norm = nn.LayerNorm(
            num_numerical
        )

        # ----------------------------------------------------
        # Final classifier
        #
        # Categorical:
        #   number of categorical features * embed_dim
        #
        # Numerical:
        #   num_numerical
        # ----------------------------------------------------

        input_dim = (
            len(cat_cardinalities) * embed_dim
            + num_numerical
        )

        # ----------------------------------------------------
        # MLP classifier
        # ----------------------------------------------------

        self.mlp = nn.Sequential(

            nn.Linear(
                input_dim,
                128
            ),

            nn.ReLU(),

            nn.Dropout(dropout),

            nn.Linear(
                128,
                64
            ),

            nn.ReLU(),

            nn.Dropout(dropout),

            nn.Linear(
                64,
                num_classes
            )

        )

    def forward(
        self,
        categorical,
        numerical
    ):

        # ----------------------------------------------------
        # Embed categorical features
        # ----------------------------------------------------

        embedded = []

        for i, embedding in enumerate(
            self.cat_embeddings
        ):

            embedded.append(

                embedding(
                    categorical[:, i]
                )

            )

        # ----------------------------------------------------
        # Shape:
        #
        # [batch_size, number_of_categories, embed_dim]
        # ----------------------------------------------------

        x = torch.stack(
            embedded,
            dim=1
        )

        # ----------------------------------------------------
        # Transformer
        # ----------------------------------------------------

        x = self.transformer(
            x
        )

        # ----------------------------------------------------
        # Flatten categorical representation
        # ----------------------------------------------------

        x = x.reshape(
            x.size(0),
            -1
        )

        # ----------------------------------------------------
        # Normalize numerical features
        # ----------------------------------------------------

        numerical = self.num_norm(
            numerical
        )

        # ----------------------------------------------------
        # Combine categorical + numerical
        # ----------------------------------------------------

        combined = torch.cat(
            [
                x,
                numerical
            ],
            dim=1
        )

        # ----------------------------------------------------
        # Classification
        # ----------------------------------------------------

        return self.mlp(
            combined
        )