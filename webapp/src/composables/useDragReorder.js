/**
 * Drag & Drop and Touch Reorder Composable
 * Handles drag and drop, touch, and button-based reordering of lists
 */
import { ref } from 'vue'

export function useDragReorder(onReorder) {
  const dragIndex = ref(null)
  const dragOverIndex = ref(null)

  const handleDragStart = (event, index) => {
    dragIndex.value = index
    if (event?.dataTransfer) {
      event.dataTransfer.effectAllowed = 'move'
      event.dataTransfer.setData('text/plain', index.toString())
    }
  }

  const handleDragEnd = () => {
    dragIndex.value = null
    dragOverIndex.value = null
  }

  const handleDragOver = (event, index) => {
    if (event) event.preventDefault()
    dragOverIndex.value = index
  }

  const handleDrop = async (event, toIndex, items) => {
    if (event) event.preventDefault()
    const fromIndex = dragIndex.value

    if (fromIndex === null || fromIndex === toIndex || !items) {
      handleDragEnd()
      return null
    }

    const reordered = [...items]
    const [movedItem] = reordered.splice(fromIndex, 1)
    reordered.splice(toIndex, 0, movedItem)

    handleDragEnd()

    if (onReorder) {
      await onReorder(reordered, fromIndex, toIndex)
    }

    return reordered
  }

  const moveUp = async (items, index) => {
    if (index <= 0 || !items || index >= items.length) return null
    const reordered = [...items]
    const [item] = reordered.splice(index, 1)
    reordered.splice(index - 1, 0, item)

    if (onReorder) {
      await onReorder(reordered, index, index - 1)
    }
    return reordered
  }

  const moveDown = async (items, index) => {
    if (!items || index < 0 || index >= items.length - 1) return null
    const reordered = [...items]
    const [item] = reordered.splice(index, 1)
    reordered.splice(index + 1, 0, item)

    if (onReorder) {
      await onReorder(reordered, index, index + 1)
    }
    return reordered
  }

  return {
    dragIndex,
    dragOverIndex,
    handleDragStart,
    handleDragEnd,
    handleDragOver,
    handleDrop,
    moveUp,
    moveDown
  }
}

export default useDragReorder
