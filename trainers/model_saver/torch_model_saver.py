import os
import shutil
from mlagents.torch_utils import torch
from typing import Dict, Union, Optional, cast, Tuple, List
from mlagents_envs.exception import UnityPolicyException
from mlagents_envs.logging_util import get_logger
from mlagents.trainers.model_saver.model_saver import BaseModelSaver
from mlagents.trainers.settings import TrainerSettings, SerializationSettings
from mlagents.trainers.policy.torch_policy import TorchPolicy
from mlagents.trainers.optimizer.torch_optimizer import TorchOptimizer
from mlagents.trainers.torch.model_serialization import ModelSerializer


logger = get_logger(__name__)
DEFAULT_CHECKPOINT_NAME = "checkpoint.pt"


class TorchModelSaver(BaseModelSaver):
    """
    ModelSaver class for PyTorch
    """

    def __init__(
        self, trainer_settings: TrainerSettings, model_path: str, load: bool = False, load_critic_only: bool = False
    ):
        super().__init__()
        self.model_path = model_path
        self.initialize_path = trainer_settings.init_path
        self._keep_checkpoints = trainer_settings.keep_checkpoints
        self.load = load
        self.load_critic_only = load_critic_only

        self.policy: Optional[TorchPolicy] = None
        self.exporter: Optional[ModelSerializer] = None
        self.modules: Dict[str, torch.nn.Modules] = {}

    def register(self, module: Union[TorchPolicy, TorchOptimizer]) -> None:
        if isinstance(module, TorchPolicy) or isinstance(module, TorchOptimizer):
            self.modules.update(module.get_modules())  # type: ignore
        else:
            raise UnityPolicyException(
                "Registering Object of unsupported type {} to ModelSaver ".format(
                    type(module)
                )
            )
        if self.policy is None and isinstance(module, TorchPolicy):
            self.policy = module
            self.exporter = ModelSerializer(self.policy)

    def save_checkpoint(self, behavior_name: str, step: int) -> Tuple[str, List[str]]:
        if not os.path.exists(self.model_path):
            os.makedirs(self.model_path)
        checkpoint_path = os.path.join(self.model_path, f"{behavior_name}-{step}")
        state_dict = {
            name: module.state_dict() for name, module in self.modules.items()
        }
        pytorch_ckpt_path = f"{checkpoint_path}.pt"
        export_ckpt_path = f"{checkpoint_path}.onnx"
        torch.save(state_dict, f"{checkpoint_path}.pt")
        torch.save(state_dict, os.path.join(self.model_path, DEFAULT_CHECKPOINT_NAME))
        self.export(checkpoint_path, behavior_name)
        return export_ckpt_path, [pytorch_ckpt_path]

    def export(self, output_filepath: str, behavior_name: str) -> None:
        if self.exporter is not None:
            self.exporter.export_policy_model(output_filepath)

    def initialize_or_load(self, policy: Optional[TorchPolicy] = None) -> None:
        # Initialize/Load registered self.policy by default.
        # If given input argument policy, use the input policy instead.
        # This argument is mainly for initialization of the ghost trainer's fixed policy.
        #reset_steps = not (self.load or self.load_critic_only)
        reset_steps = not self.load
        if self.initialize_path is not None:
            logger.info(f"Initializing from {self.initialize_path}.")
            self._load_model(
                self.initialize_path, policy, reset_global_steps=reset_steps
            )
        elif self.load_critic_only:
            logger.info(f"Loading critic only from {self.model_path}.")
            self._load_model(
                os.path.join(self.model_path, DEFAULT_CHECKPOINT_NAME),
                policy,
                reset_global_steps=reset_steps,
                load_critic_only=self.load_critic_only,
            )
        elif self.load:
            logger.info(f"Resuming from {self.model_path}.")
            self._load_model(
                os.path.join(self.model_path, DEFAULT_CHECKPOINT_NAME),
                policy,
                reset_global_steps=reset_steps,
                load_critic_only=False,
            )

    def _load_model(
        self,
        load_path: str,
        policy: Optional[TorchPolicy] = None,
        reset_global_steps: bool = False,
        load_critic_only: Union[bool, str] = False,
    ) -> None:
        saved_state_dict = torch.load(load_path)
        if policy is None:
            modules = self.modules
            policy = self.policy
        else:
            modules = policy.get_modules()
        policy = cast(TorchPolicy, policy)

        # TODO double check this
        for name, mod in modules.items():
            # if name.lower() == "global_step":
            #     continue
            print(f"Considering {name}")
            try:
                if load_critic_only:
                    
                    # # only use critic network
                    # if "policy" in name.lower():
                    #     logger.warning(f"Skipping {name} module due to load_critic_only")
                    #     continue
                    if "default" in load_critic_only.lower() and ("optimizer:critic" in name.lower() or "policy" in name.lower()):
                        dont_load = ['network_body', 'action_model']
                        critic_state_dict = {k: v for k, v in saved_state_dict[name].items() if not any(x in k for x in dont_load)}
                        mod.load_state_dict(critic_state_dict, strict=False)
                        logger.info(f"Loaded {name}")
                        continue

                    # only use position_network from critic network
                    # if "position_only" in load_critic_only.lower() and "optimizer:critic" in name.lower():
                    #     position_state_dict = {k: v for k, v in saved_state_dict[name].items() 
                    #                         if 'position_network' in k}
                    #     mod.load_state_dict(position_state_dict, strict=False)
                    #     logger.info("Loaded position_network only from critic")

                    #     # Load the importance network from the specified path
                    #     importance_network_path = "/home/rmarr/Projects/visibility-game-env/informed_init/bias_importance.pt"
                    #     importance_state_dict = torch.load(importance_network_path)
                    #     mod.importance_network.load_state_dict(importance_state_dict, strict=False)
                    #     logger.info("Loaded importance_network from informed_init")
                    #     continue

                if isinstance(mod, torch.nn.Module):
                    missing_keys, unexpected_keys = mod.load_state_dict(
                        saved_state_dict[name], strict=False
                    )
                    if missing_keys:
                        logger.warning(
                            f"Did not find these keys {missing_keys} in checkpoint. Initializing."
                        )
                    if unexpected_keys:
                        logger.warning(
                            f"Did not expect these keys {unexpected_keys} in checkpoint. Ignoring."
                        )
                    logger.info(f"Loaded {name}")
                else:
                    # If module is not an nn.Module, try to load as one piece
                    mod.load_state_dict(saved_state_dict[name])
                    logger.info(f"Loaded {name}")
            # KeyError is raised if the module was not present in the last run but is being
            # accessed in the saved_state_dict.
            # ValueError is raised by the optimizer's load_state_dict if the parameters have
            # have changed. Note, the optimizer uses a completely different load_state_dict
            # function because it is not an nn.Module.
            # RuntimeError is raised by PyTorch if there is a size mismatch between modules
            # of the same name. This will still partially assign values to those layers that
            # have not changed shape.
            except (KeyError, ValueError, RuntimeError) as err:
                logger.warning(f"Failed to load for module {name}. Initializing")
                logger.debug(f"Module loading error : {err}")

        if reset_global_steps:
            policy.set_step(0)
            logger.info(
                "Starting training from step 0 and saving to {}.".format(
                    self.model_path
                )
            )
        else:
            logger.info(f"Resuming training from step {policy.get_current_step()}.")

    def copy_final_model(self, source_nn_path: str) -> None:
        """
        Copy the .nn file at the given source to the destination.
        Also copies the corresponding .onnx file if it exists.
        """
        final_model_name = os.path.splitext(source_nn_path)[0]

        if SerializationSettings.convert_to_onnx:
            try:
                source_path = f"{final_model_name}.onnx"
                destination_path = f"{self.model_path}.onnx"
                shutil.copyfile(source_path, destination_path)
                logger.info(f"Copied {source_path} to {destination_path}.")
            except OSError:
                pass

    def _verify_critic(self, critic):
        """
        Verify that critic was loaded properly
        """
        # Check if weights are non-zero
        has_weights = False
        for param in critic.parameters():
            if torch.any(param != 0):
                has_weights = True
                break
        
        if not has_weights:
            raise ValueError("Critic loaded with all zero weights!")
