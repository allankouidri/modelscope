from torch import nn
from typing import Any, Dict
from ..base import Model
import numpy as np
import json
import os
from sofa.models.sbert.modeling_sbert import SbertPreTrainedModel, SbertModel


class SbertTextClassfier(SbertPreTrainedModel):

    def __init__(self, config):
        super().__init__(config)
        self.num_labels = config.num_labels
        self.config = config
        self.encoder = SbertModel(config, add_pooling_layer=True)
        self.dropout = nn.Dropout(config.hidden_dropout_prob)
        self.classifier = nn.Linear(config.hidden_size, config.num_labels)

    def forward(self, input_ids=None, token_type_ids=None):
        outputs = self.encoder(
            input_ids,
            token_type_ids=token_type_ids,
            return_dict=None,
        )
        pooled_output = outputs[1]
        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)
        return {
            "logits": logits
        }


class SbertForSequenceClassificationBase(Model):

    def __init__(self, model_dir: str, *args, **kwargs):
        super().__init__(model_dir, *args, **kwargs)
        self.model = SbertTextClassfier.from_pretrained(model_dir)
        self.id2label = {}
        self.label_path = os.path.join(self.model_dir, 'label_mapping.json')
        if os.path.exists(self.label_path):
            with open(self.label_path) as f:
                self.label_mapping = json.load(f)
            self.id2label = {idx: name for name, idx in self.label_mapping.items()}

    def forward(self, input: Dict[str, Any]) -> Dict[str, np.ndarray]:
        return self.model.forward(input)

    def postprocess(self, input, **kwargs):
        logits = input["logits"]
        probs = logits.softmax(-1).numpy()
        pred = logits.argmax(-1).numpy()
        logits = logits.numpy()
        res = {'predictions': pred, 'probabilities': probs, 'logits': logits}
        return res
