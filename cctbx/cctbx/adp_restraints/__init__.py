from cctbx.array_family import flex

import boost.python
ext = boost.python.import_ext("cctbx_adp_restraints_ext")
from cctbx_adp_restraints_ext import *

from cctbx import crystal
from cctbx import adptbx
import scitbx.restraints

class energies_iso(scitbx.restraints.energies):

  def __init__(self,
        geometry_restraints_manager,
        xray_structure,
        parameters,
        wilson_b=None,
        compute_gradients=True,
        gradients=None,
        normalization=False,
        collect=False):
    assert geometry_restraints_manager.plain_pair_sym_table is not None
    assert geometry_restraints_manager.plain_pairs_radius is not None
    assert parameters.sphere_radius \
        <= geometry_restraints_manager.plain_pairs_radius
    scitbx.restraints.energies.__init__(self,
      compute_gradients=compute_gradients,
      gradients=gradients,
      gradients_size=xray_structure.scatterers().size(),
      gradients_factory=flex.double,
      normalization=normalization)
    unit_cell = xray_structure.unit_cell()
    u_isos = xray_structure.extract_u_iso_or_u_equiv()
    energies = crystal.adp_iso_local_sphere_restraints_energies(
      pair_sym_table=geometry_restraints_manager.plain_pair_sym_table,
      orthogonalization_matrix=unit_cell.orthogonalization_matrix(),
      sites_frac=xray_structure.sites_frac(),
      u_isos=u_isos,
      sphere_radius=parameters.sphere_radius,
      distance_power=parameters.distance_power,
      mean_power=parameters.mean_power,
      min_u_sum=1.e-6,
      compute_gradients=compute_gradients,
      collect=collect)
    self.number_of_restraints += energies.number_of_restraints
    self.residual_sum += energies.residual_sum
    if (compute_gradients):
      self.gradients += energies.gradients
    if (not collect):
      self.u_i = None
      self.u_j = None
      self.r_ij = None
    else:
      self.u_i = energies.u_i
      self.u_j = energies.u_j
      self.r_ij = energies.r_ij
    if (    wilson_b is not None
        and wilson_b > 0
        and parameters.wilson_b_weight is not None
        and parameters.wilson_b_weight > 0):
      wilson_u = adptbx.b_as_u(wilson_b)
      u_diff = flex.mean(u_isos) - wilson_u
      self.number_of_restraints += 1
      self.residual_sum += parameters.wilson_b_weight * u_diff**2 / wilson_u
      if (compute_gradients):
        g_wilson = 2. * parameters.wilson_b_weight * u_diff \
                 / u_isos.size() / wilson_u
        self.gradients += g_wilson
    self.finalize_target_and_gradients()
