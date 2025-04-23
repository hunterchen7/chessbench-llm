import React from "react";

const Modal = ({ isOpen, onClose, children }: { isOpen: boolean, onClose: () => void, children: React.ReactNode }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 flex items-center justify-center z-50">
      <div className="fixed inset-0 bg-black opacity-50" onClick={onClose}></div>
      <div className="rounded-lg shadow-lg p-0 z-10 w-1/2 ">
        {children}
      </div>
    </div>
  );
}

export default Modal;